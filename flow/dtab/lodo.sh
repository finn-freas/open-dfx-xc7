#!/usr/bin/env bash
set -u
R=/home/finnf/open-dfx-xc7
O=$R/build/dtab
cd "$R/flow/dtab" || exit 1
for d in rv_soc bram rv_big rv_mul; do
  (
    [ -f "$O/t_lodo_$d.txt" ] || python3 fit.py "$O/t_lodo_$d.txt" --fo --train "^(?!${d}_).*_s[12456]_exact\$" > "$O/fit_lodo_$d.log" 2>&1
    DTAB="$O/t_lodo_$d.txt" python3 measure.py "^${d}_p5_ua_dxy(_dq)?_s[1-6]_exact\$" dtab:m_tab dtab:m_fo > "$O/lodo_$d.md" 2>&1
    DTAB="$O/t_lodo_$d.txt" python3 pathlev.py "^${d}_.*_s3_exact\$" 50 > "$O/lodo_path_$d.md" 2> "$O/lodo_path_$d.log"
  ) &
done
wait
echo LODO_DONE
