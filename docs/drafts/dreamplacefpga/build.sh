D=$HOME/open-dfx-xc7/toolchain/dreamplacefpga
E=$D/env
export PATH=$E/bin:$PATH
cd $D
$E/bin/pip install -q pyunpack patool > pip.log 2>&1; echo pip rc=$?
ABI=$($E/bin/python -c "import torch; print(int(torch._C._GLIBCXX_USE_CXX11_ABI))")
echo torch $($E/bin/python -c "import torch; print(torch.__version__)") abi=$ABI
until [ $(free -m | awk '/Mem:/{print $7}') -ge 4000 ]; do sleep 30; done
mkdir -p build
cd build
export CFLAGS="-I$E/include" CXXFLAGS="-I$E/include" LDFLAGS="-L$E/lib -Wl,-rpath,$E/lib"
export CC=$E/bin/x86_64-conda-linux-gnu-gcc CXX=$E/bin/x86_64-conda-linux-gnu-g++
cmake ../src -DCMAKE_INSTALL_PREFIX=$D/install -DPYTHON_EXECUTABLE=$E/bin/python -DCMAKE_CXX_ABI=$ABI \
  -DBOOST_ROOT=$E -DCMAKE_PREFIX_PATH=$E -DCMAKE_DISABLE_FIND_PACKAGE_CUDA=ON > ../cmake.log 2>&1
echo cmake rc=$?
tail -5 ../cmake.log
make -j2 > ../make.log 2>&1
echo make rc=$?
grep -E "error|Error" ../make.log | head -20
make install > ../install.log 2>&1
echo install rc=$?
