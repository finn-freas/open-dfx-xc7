# Comment-free publish (`tools/publish_strip.py`)

The GitHub repository receives a comment-free export of master. Comments are fine in the local
repository; only the `publish` branch is pushed. The export removes comments and nothing else, and it
proves this for every file before the branch moves.

## Running it

```sh
python3 tools/publish_strip.py              # export HEAD, strip, all proofs, then commit to `publish`
python3 tools/publish_strip.py --skip-e2e   # every proof except the builds (f); the branch is not touched
python3 tools/publish_strip.py --no-branch  # every proof, the branch is not touched
python3 tools/publish_strip.py --rev <sha>  # export another commit
```

The script exits 1, and leaves the branch where it is, when a proof fails. The output is in
`build/publish/`:

| path | content |
|---|---|
| `tree/` | the stripped export (what the publish commit holds) |
| `orig/` | the unmodified `git archive` of the same commit |
| `report.json` | per-file results, counts per language, kept comments, unknown files, series and end-to-end results |
| `e2e/` | the end-to-end build log, the saved `.frames`/partials, and `result_<origtree>_<striptree>.json` |
| `publish_map.txt` | `<publish commit> <master commit>` per publish |

Pushing stays a manual step: `git push --force origin publish:master` once (the first publish commit is a
root commit, so this rewrites GitHub's history), then `git push origin publish:master` afterwards.

## What is stripped

The export comes from `git archive <rev>`, so untracked and gitignored files (`BRIEF.md`, `build/`,
`toolchain/`) are never published; the script also fails if `BRIEF.md` is tracked.

Each file is classified by name, extension, or shebang:

| language | files | comments |
|---|---|---|
| Python | `.py`, extensionless files with a python shebang | `tokenize` COMMENT tokens; docstrings stay |
| shell | `.sh`, `.bash`, sh/bash shebang | `#` at the start of a word, outside quotes, `$#`, `${#x}`, `${x#y}`, `$((16#ff))`, `$(...)` aware; heredoc bodies are data |
| Verilog | `.v`, `.sv`, `.vh`, `.svh` | `//` and `/* */`, outside strings and escaped identifiers; `(* *)` attributes are not comments |
| VHDL | `.vhd`, `.vhdl` | `--` and `/* */` |
| Tcl/XDC | `.tcl`, `.xdc`, `.sdc` | `#` where Tcl starts a command (line start, after `;`), also inside `proc`/`if`/`foreach`/`for`/`while`/`catch`/`switch` bodies |
| PowerShell | `.ps1`, `.psm1` | `#` and `<# #>` |
| C, C++, assembly, linker | `.c .h .cc .cpp .hpp .inc .pmg .S .s .ld` | `//` and `/* */`; `.s` (RISC-V) also `#`; `.S` ARM files also `@`; `.ld` only `/* */` |
| config | `.toml .yaml .cfg .ini`, CMake, Makefile, Dockerfile, `.gitignore` | `#` (and `;` for ini) by each format's rule |
| patches | `.patch`, `.diff` | only comment text inside `+` lines, lexed with the target file's language |

Data and documents are not touched: `.md .txt .json .csv .hex .init .segbits .ppips .lock`, `VERSION`,
`TREE`, `SERIES`, empty files. Anything else is left as it is and listed under `unknown_untouched`.

Kept on purpose (listed under `kept_functional`): shebangs, Python encoding lines, Verilog/VHDL tool
pragmas (`/* synthesis ... */`, `/* verilator ... */`, `translate_off`, ...), PowerShell `#requires`,
Dockerfile parser directives, and licence notices of third-party code (comments containing
"Copyright", "SPDX-License-Identifier", "Permission is hereby granted", ...), because the licences
require the notice to stay with the code.

Deletion rule: the comment, and the blanks directly in front of it, are deleted. A line that held only a
comment is deleted with its newline (unless that would join two lines of code). Nothing is inserted,
nothing is reformatted. In patches a comment-only `+` line becomes an empty `+` line, so hunk headers and
line numbers in the patched sources stay valid.

Patch series (`install/patches/{nextpnr,yosys,openfpgaloader}/0*.patch`) are applied in order by
`install.sh`. When a later patch has a context or `-` line that repeats a `+` line of an earlier patch
of the same series, that line gets the same stripped form, otherwise the stripped series would not apply.
`install.sh` checks the patched tree against `install/patches/<name>/TREE`; that checksum follows the
patches, so the export writes the tree id of the stripped series into `TREE` (only after the series proof
below passed and only if the old `TREE` was the tree of the original series). The report lists each
such update.

## Proofs (the branch moves only when all pass)

- **(a) only comments removed**, every changed file: the stripped text must be identical to a second,
  independent line-oriented recomputation from the original and the lexer's comment spans, and the
  token structure (words per line for line-oriented languages, words otherwise) of the original with
  comments blanked must equal that of the stripped file. Patches: line count and hunk structure are
  unchanged, only `+` lines (and mapped series context lines) differ, each hunk's new side passes (a).
- **(b) Python**: `ast.dump` of original and stripped is equal.
- **(c) Verilog**: yosys `read_verilog -sv` (include path: the file's directory and the repository root)
  then `write_rtlil`; equal after dropping `src` attributes and `file:line` inside generated names.
  A file that does not elaborate on its own is compared after `read_verilog -defer`.
- **(d) shell**: `bash -n` on both, and `bash --pretty-print` (bash's own parse, without comments) is
  identical.
- **(e) Tcl/XDC**: `tclsh` splits each file into commands with `info complete` (recursing into script
  bodies and `[...]` substitutions); the stripped file parses and the command lists are equal.
- **series**: each series is applied with `git am` on the pinned rev from `install/sources.toml`
  (source clones from the ofx install cache), original and stripped; every file that differs must have
  the same line count and differ only by comment text.
- **(f) end to end**: blinky and rv_soc (`flow/build_openxc7.py`) and rv_pr (`bin/ofx dfx build`) are
  built from a copy of the stripped tree (toolchain and nextpnr builds linked in; nextpnr through
  `ofx/npwait.sh`) and their `.frames` compared with the cached original builds; if a cached build is
  missing or differs, the original tree is built at the same path and compared. The result is cached
  per (original tree, stripped tree) pair.
- **(g) final scan**: the lexers find no comment left in any code file of the export, apart from the
  kept ones above.

## The publish branch

Built with plumbing only (`hash-object -w`, `update-index --index-info` into a temporary
`GIT_INDEX_FILE`, `write-tree`, `commit-tree`, `update-ref`); the working tree, the index and master are
not touched. Unchanged files reuse master's blobs and modes. The first commit has no parent; later ones
have the previous publish tip as parent. The message lists the master commits since the last publish and
ends with `Source-Commit: <master sha>`; a run on an already published master does nothing.
