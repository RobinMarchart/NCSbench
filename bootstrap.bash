if test -d ~/.pyenv; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
else
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv;if 0 -ne $?;then exit $?;fi
    git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv;if 0 -ne $?;then exit $?;fi

    echo "installing dev dependencies"
    sudo apt-get update;if 0 -ne $?;then exit $?;fi
    sudo apt-get install --no-install-recommends -y make build-essential zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev\
        ;if 0 -ne $?;then exit $?;fi

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
        curl https://www.openssl.org/source/openssl-1.1.1d.tar.gz --output /tmp/openssl/openssl-1.1.1d.tar.gz;if 0 -ne $?;then exit $?;fi
    fi
    pushd /tmp/openssl
    tar -xz -f openssl-1.1.1d.tar.gz;if 0 -ne $?;then exit $?;fi
    cd openssl-1.1.1d
    ./config --prefix=$(realpath ~/.pyenv/openssl) --openssldir=$(realpath ~/.pyenv/openssldir);if 0 -ne $?;then exit $?;fi
    make;if 0 -ne $?;then exit $?;fi
    make test;if 0 -ne $?;then exit $?;fi
    make install;if 0 -ne $?;then exit $?;fi
    popd
    touch ~/.pyenv/openssl_compiled
fi

export PATH=$HOME/openssl/bin:$PATH
export LD_LIBRARY_PATH=$HOME/openssl/lib
export LDFLAGS="-L$(realpath ~)/.pyenv/openssl/lib -Wl,-rpath,$(realpath ~)/.pyenv/openssl/lib"

if ! test -d ~/.pyenv/versions/3.7.5; then
    export CONFIGURE_OPTS="--with-openssl=$(realpath ~/.pyenv/openssl)"
    pyenv install 3.7.5;if 0 -ne $?;then exit $?;fi
    pyenv local 3.7.5;if 0 -ne $?;then exit $?;fi
fi

if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
fi
eval "$(pyenv virtualenv-init -)"

if ! test -d ~/.pyenv/versions/3.7.5/envs/NCSbench; then
    pyenv virtualenv 3.7.5 NCSbench;if 0 -ne $?;then exit $?;fi
fi

source activate NCSbench

installed=$(python3 -m pip freeze)

if [[ $installed != *"wheel"* ]]; then
    pip install wheel;if 0 -ne $?;then exit $?;fi
fi

#pip install -r src/requirements.txt
if [[ $installed != *"ncsbench"* ]]; then
    cd src
    ./setup.py develop;if 0 -ne $?;then exit $?;fi
    cd ..
fi
