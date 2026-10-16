# -*- coding: utf-8 -*-
"""Parse the .NET #US (user strings) heap of Assembly-CSharp.dll.

Empirically decodes each blob: compressed-uint size prefix + UTF-16LE data
(+ optional trailing flag byte). Provides dump/patch helpers.
"""
import struct, sys

DLL = r"D:\Steam\steamapps\common\Erannorth Reborn\Erannorth Reborn_Data\Managed\Assembly-CSharp.dll"

def read_compressed_uint(buf, i):
    b = buf[i]
    if b & 0x80 == 0:
        return b, i + 1
    if b & 0xC0 == 0x80:
        return ((b & 0x3F) << 8) | buf[i+1], i + 2
    return ((b & 0x1F) << 24) | (buf[i+1] << 16) | (buf[i+2] << 8) | buf[i+3], i + 4

def parse(buf):
    """Return (us_start, us_size, [(offset, total_len, prefix_len, blob_bytes), ...])."""
    # PE
    assert buf[:2] == b'MZ'
    pe = struct.unpack_from('<I', buf, 0x3C)[0]
    assert buf[pe:pe+4] == b'PE\0\0'
    nsec = struct.unpack_from('<H', buf, pe + 6)[0]
    opt_size = struct.unpack_from('<H', buf, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from('<H', buf, opt)[0]
    pe32plus = magic == 0x20B
    ndd = struct.unpack_from('<I', buf, opt + (108 if not pe32plus else 112))[0]
    cli_rva = struct.unpack_from('<I', buf, opt + (208 if not pe32plus else 224))[0]
    # section table
    secs = []
    st = opt + opt_size
    for k in range(nsec):
        name = buf[st:st+8].rstrip(b'\0').decode()
        vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', buf, st + 8)
        secs.append((name, vaddr, vsize, raddr, rsize))
        st += 40
    def rva2off(rva):
        for name, va, vs, ra, rs in secs:
            if va <= rva < va + max(vs, rs):
                return ra + (rva - va)
        raise ValueError(hex(rva))
    # CLI header
    md_rva = struct.unpack_from('<I', buf, rva2off(cli_rva) + 8)[0]
    md = rva2off(md_rva)
    # metadata root: signature 0x424A5342, then version len etc.
    assert struct.unpack_from('<I', buf, md)[0] == 0x424A5342
    ver_len = struct.unpack_from('<I', buf, md + 12)[0]
    ver_len += (4 - ver_len % 4) % 4  # padded
    nstreams = struct.unpack_from('<H', buf, md + 16 + ver_len + 2)[0]
    sh = md + 16 + ver_len + 2 + 2
    streams = {}
    for k in range(nstreams):
        off, size = struct.unpack_from('<II', buf, sh)
        nm_end = buf.index(b'\0', sh + 8)
        nm = buf[sh+8:nm_end].decode()
        streams[nm] = (md + off, size)
        sh = (nm_end + 4) & ~3  # name padded to 4
    us_start, us_size = streams['#US']
    blobs = []
    i = 1  # first byte of #US is the empty-string entry (0x00)
    while i < us_size:
        size, p = read_compressed_uint(buf, us_start + i)
        if size == 0:
            blobs.append((i, p - (us_start + i), 0, b''))
            i = p - us_start
            continue
        data = buf[p:p+size]
        blobs.append((i, p - (us_start + i), size, data))
        i = (p + size) - us_start
    return us_start, us_size, blobs

def decode(data):
    """Decode blob data -> python string (None if not decodable as string).

    Empirically (this file): data = N chars as full UTF-16LE + 1 flag byte (0x00/0x01).
    No compressed last char exists (all cores are even-length; verified).
    """
    if len(data) == 0:
        return ''
    core, flag = data[:-1], data[-1]
    if len(core) % 2 == 0 and flag in (0, 1):
        try:
            return core.decode('utf-16-le')
        except UnicodeDecodeError:
            return None
    return None

def encode(s, orig_data):
    """Encode string s into blob data with the exact same byte length.
    The trailing flag byte is preserved verbatim."""
    core = s.encode('utf-16-le')
    assert len(core) == len(orig_data) - 1, "length mismatch"
    return core + orig_data[-1:]

if __name__ == '__main__':
    buf = bytearray(open(DLL, 'rb').read())
    us_start, us_size, blobs = parse(bytes(buf))
    print(f"#US heap at file offset {us_start:#x}, size {us_size:#x}, {len(blobs)} blobs")
    # sanity: decode a few known strings
    hits = 0
    for off, plen, size, data in blobs:
        s = decode(data)
        if s is not None and s in ('Accept', 'Continue', 'Deck', 'Ambushed!', "Choose & Draw"):
            print(f"  found {s!r}: off={off:#x} prefix={plen} size={size} data={data.hex()}")
            hits += 1
    print("known-string hits:", hits)
    # stats
    decodable = sum(1 for _,_,_,d in blobs if decode(d) is not None)
    print(f"decodable blobs: {decodable}/{len(blobs)}")
