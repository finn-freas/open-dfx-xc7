D=$HOME/open-dfx-xc7/toolchain/dreamplacefpga
export MAMBA_ROOT_PREFIX=$D/mm/root
cd $D
cat > $D/mm/root/.mambarc <<'EOF'
use_sharded_repodata: false
download_threads: 2
remote_max_retries: 6
EOF
./mm/bin/micromamba create -y --rc-file $D/mm/root/.mambarc -p $D/env -c conda-forge --override-channels \
  "python=3.8" "pytorch=1.8.*=cpu*" "numpy<1.24" scipy matplotlib cairocffi pkgconfig python-igraph pycapnp \
  cmake make "boost-cpp" flex bison "gxx_linux-64=9" "gcc_linux-64=9" "sysroot_linux-64=2.17" zlib > $D/env_create.log 2>&1
echo rc=$? >> $D/env_create.log
tail -40 $D/env_create.log | cut -c1-200
