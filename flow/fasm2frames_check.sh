cd ~/open-dfx-xc7
T=$PWD/toolchain/openxc7
export PATH=$T/bin:$PATH PYTHONEXECUTABLE=$T/libexec/tabbypy3
O=build/runtime/prof/f2f_check; mkdir -p $O; : > $O/result.txt
(ls -d build/qor/oxc7/*/*/s1/*.fasm | awk "NR%7==1" | head -25; ls -d build/rt_rv_pr_on/build/dfx/router/*/*.fasm build/eth/arty_eth/*/*.fasm build/ddr3/arty_ddr3/*/*.fasm 2>/dev/null) > $O/list.txt
while read f; do
  case "$f" in *mc12_a100*) part=xc7a100tcsg324-1;; *) part=xc7a35tcsg324-1;; esac
  DB=$T/share/nextpnr/external/prjxray-db/artix7
  $T/bin/fasm2frames --part $part --db-root $DB $f > $O/o.frames 2>$O/o.err; ro=$?
  $T/libexec/tabbypy3 flow/fasm2frames_fast.py $T/libexec/fasm2frames --part $part --db-root $DB $f > $O/f.frames 2>$O/f.err; rf=$?
  if [ $ro = $rf ] && cmp -s $O/o.frames $O/f.frames && cmp -s $O/o.err $O/f.err; then echo "SAME rc=$ro $f" >> $O/result.txt; else echo "DIFF rc=$ro/$rf $f" >> $O/result.txt; fi
done < $O/list.txt
rm -f $O/o.frames $O/f.frames
sort $O/result.txt | cut -c1-4 | uniq -c
