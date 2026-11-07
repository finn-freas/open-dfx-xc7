"""Runs the toolchain's own fasm2frames (prjxray) in this interpreter with one hot spot replaced.

Run it with the toolchain Python (libexec/tabbypy3), with the same arguments as fasm2frames:
    tabbypy3 flow/fasm2frames_fast.py <toolchain>/libexec/fasm2frames --part P --db-root D in.fasm [out.frames]

FasmAssembler.enable_feature() adds every frame of a tile to frames_in_use again for every feature set in that
tile (about 2.3 million set.add calls on rv_soc). The set only grows, so adding each (tile, block type) once
gives the same set. Everything else is the original code, and the result is checked byte for byte against
the original on every .fasm in the repo by flow/fasm2frames_check.sh (docs/runtime.md).
"""
import runpy
import sys

from prjxray import bitstream, fasm_assembler

WORD = bitstream.WORD_SIZE_BITS


def enable_feature(self, tile, feature, address, line):
    gridinfo = self.grid.gridinfo_at_tilename(tile)
    segbits = self.grid.get_tile_segbits_at_tilename(tile)
    self.seen_tile.add(tile)
    db_k = '%s.%s' % (gridinfo.tile_type, feature)
    any_bits = set()
    try:
        for block_type, bit in segbits.feature_to_bits(gridinfo.bits, db_k, address):
            any_bits.add(block_type)
            frame_addr = bit.word_column
            word_addr = bit.word_bit // WORD
            bit_index = bit.word_bit % WORD
            if bit.isset:
                self.frame_set(frame_addr, word_addr, bit_index, line)
            else:
                self.frame_clear(frame_addr, word_addr, bit_index, line)
    except KeyError:
        raise fasm_assembler.FasmLookupError(
            "Segment DB %s, key %s not found from line '%s'" % (gridinfo.tile_type, db_k, line))
    done = self.__dict__.setdefault("_frames_in_use_done", set())
    for block_type in any_bits:
        k = (tile, block_type)
        if k in done:
            continue
        done.add(k)
        bits = gridinfo.bits[block_type]
        self.frames_in_use.update(range(bits.base_address, bits.base_address + bits.frames))


def main():
    script = sys.argv[1]
    fasm_assembler.FasmAssembler.enable_feature = enable_feature
    sys.argv = [script] + sys.argv[2:]
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
