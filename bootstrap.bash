if test -d ~/.pyenv; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
else
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv

    echo "installing dev dependencies"
    sudo -B apt-get update
    sudo -B apt-get install --no-install-recommends -y make build-essential zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
fi
#openssl_version=$(openssl version | sed -n "s/^.*SSL\s*\(\S*\).*$/\1/p")
if ! test -e ~/.pyenv/openssl_compiled; then
    if test -d ~/.pyenv/openssl; then
        rm -rf ~/.pyenv/openssl
    fi
    if test -d ~/.pyenv/openssldir; then
        rm -rf ~/.pyenv/openssldir
    fi
    echo "compiling openssl-1.1.1d"
    if test -d /tmp/openssl/openssl-1.1.1d.tar.gz; then
        echo "using cached /tmp/openssl/openssl-1.1.1d.tar.gz"
    else
        mkdir /tmp/openssl
        curl https://www.openssl.org/source/openssl-1.1.1d.tar.gz --output /tmp/openssl/openssl-1.1.1d.tar.gz
    fi
    pushd /tmp/openssl
    tar -xz -f openssl-1.1.1d.tar.gz
    cd openssl-1.1.1d
    ./config --prefix=$(realpath ~/.pyenv/openssl) --openssldir=$(realpath ~/.pyenv/openssldir)
    make
    make install
    popd
    touch ~/.pyenv/openssl_compiled
fi

PATH=$HOME/openssl/bin:$PATH
LD_LIBRARY_PATH=$HOME/openssl/lib
LC_ALL="en_US.UTF-8"
LDFLAGS="-L$(realpath ~)/.pyenv/openssl/lib -Wl,-rpath,$(realpath ~)/.pyenv/openssl/lib"

if ! test -d ~/.pyenv/versions/3.7.5; then
    CONFIGURE_OPTS="--help --with-openssl=$(realpath ~/.pyenv/openssl)"
    CFLAGS="-I$(realpath ~/.pyenv/openssl/include)"
    LDFLAGS="-L$(realpath ~/.pyenv/openssl/lib)"
    pyenv install 3.7.5
    pyenv local 3.7.5
fi

if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
fi
eval "$(pyenv virtualenv-init -)"

if ! test -d ~/.pyenv/versions/3.7.5/envs/NCSbench; then
    pyenv virtualenv 3.7.5 NCSbench
fi

source activate NCSbench

installed=python3 -m pip freeze

if [[ $installed == *"wheel"* ]]; then
    pip install wheel
fi

#pip install -r src/requirements.txt
if [[ $installed == *"ncsbench"* ]]; then
    cd src
    ./setup.py develop
    cd ..
fi
