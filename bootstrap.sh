if test -d ~/.pyenv
then 
    echo "pyenv already exists"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
else
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv

echo "installing dev dependencies"
sudo apt-get update
sudo apt-get install --no-install-recommends -y make build-essential libssl-dev zlib1g-dev libbz2-dev\
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
    
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

pyenv install 3.7.5

pyenv local 3.7.5
fi


if command -v pyenv 1>/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi
eval "$(pyenv virtualenv-init -)"

if test -d venv3.7.5
then
    echo ""
else
    pyenv virtualenv 3.7.5 venv3.7.5
fi

source activate venv3.7.5

pip install wheel

#pip install -r src/requirements.txt
cd src
./setup.py develop
cd ..
