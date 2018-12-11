#!/bin/bash
set -e

cd "$(dirname "$0")"

uname_out="$(uname -s)"
case "${uname_out}" in
    Linux*)     C_OS_TYPE=Linux;;
    Darwin*)    C_OS_TYPE=Mac;;
    *)          C_OS_TYPE="UNKNOWN:${uname_out}"
esac

C_PROJECT_NAME=${PWD##*/}

main() {
    local CMD=$1
    shift
    echo -e "Run $C_PROJECT_NAME on $C_OS_TYPE\\n"

    case $CMD in
        setup) setup "$@";;
        build) build "$@";;
        stack) stack "$@";;
        test) test "$@";;
        generate) generate "$@";;
        clean) clean "$@";;
        *) echo "Run as: $0 command
Possible commands:
    setup    check/install host prerequisties
    stack    run the specified stack
    test     run tests
    generate generate configuration files for the current environment
    clean    clean the stack
    docker   docker operations
    setenv   export variable to env
    upgrade  apply upgrade scripts
    "; exit;;
    esac
}


setup() {
    local DOCKER_VERSION=${1:-17.12}
    apt-get update -qq
    apt-get install -y curl apt-transport-https

    mkdir -p /etc/docker

    echo '{
        "log-driver": "json-file",
        "log-opts": {
            "max-size": "10m",
            "max-file": "2"
        }
    }' > /etc/docker/daemon.json

    echo "Installing Docker..."

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    apt install -y software-properties-common
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) \
        stable"
    apt-get update -qq
    apt-get install -y docker-ce="$(apt-cache madison docker-ce | grep "$DOCKER_VERSION" | head -1 | awk '{print $3}')"
    apt-get install python-pip -y
    pip install docker-compose

    systemctl restart docker

    echo "Done"
}

check_stack() {
    local STACK=$1
    shift

    if [[ ! "$STACK" =~ ^(dev|stage|prod|test)$ ]]; then
        echo "$0 stack [dev|stage|prod|test]";
        exit 1
    fi
}

stack() {
    local STACK=dev

    if [[ "$#" -gt 0 ]]; then
        local STACK=$1
        shift
    fi

    check_stack "$STACK"

    C_PROJECT_STACK=$STACK

    generate_compose "$STACK"
    docker_build

    mkdir -p "tmp/coverage";

    docker-compose up -d

    echo "Done"
}

clean() {
    docker-compose down -v --remove-orphans
    docker-compose rm -fv

    docker images --format '{{.Repository}}' | grep "$C_PROJECT_NAME" | xargs docker rmi
}

generate() {
    local CMD=$1
    shift

    case $CMD in
        compose) generate_compose "$@";;
        *) echo "$0 generate [compose]"; exit;;
    esac
}

generate_compose() {
    local STACK=dev

    if [[ "$#" -gt 0 ]]; then
        local STACK=$1
        shift
    fi

    check_stack "$STACK"

    export C_PROJECT_STACK=$STACK

    local DOCKER_COMPOSE_YAML=build/docker-compose.$STACK.yaml
    if [[ ! -f $DOCKER_COMPOSE_YAML ]] ; then
        DOCKER_COMPOSE_YAML=build/docker-compose.yaml
    fi

    rm -f docker-compose.yaml
    cp $DOCKER_COMPOSE_YAML docker-compose.yaml

    for env_variable in C_PROJECT_NAME \
                        C_PROJECT_VERSION \
                        C_PROJECT_STACK; do
        if [[ ${!env_variable} ]]; then
            # FIXME: sed a little bit differs on Mac OS X
            if [[ "$C_OS_TYPE" == 'Linux' ]]; then
                sed -i "s~__${env_variable}__~${!env_variable}~g" docker-compose.yaml
            else
                sed -i '' "s~__${env_variable}__~${!env_variable}~g" docker-compose.yaml
            fi
        fi
    done
}

coverage() {
    local CMD=$1
    shift

    case $CMD in
        report) coverage_report "$@";;
        clean) coverage_clean "$@";;
        *) echo "$0 coverage [report|clean]"; exit;;
    esac
}

coverage_report() {
    local COVERAGE_RCFILE=.coveragerc
    local COVERAGE_DATA=tmp/coverage/

    docker-compose run \
        --rm test sh -c "coverage combine --rcfile=$COVERAGE_RCFILE $COVERAGE_DATA && coverage report --rcfile=$COVERAGE_RCFILE && coverage html --rcfile=$COVERAGE_RCFILE"
}

coverage_clean() {
    docker-compose run \
        --rm test rm -rf "tmp/coverage";
    mkdir -p "tmp/coverage";
}

test() {
    local CMD=$1
    shift

    case $CMD in
        style) test_style "$@";;
        functional) test_functional "$@";;
        unit) test_unit "$@";;
        ci) test_ci "$@" ;;
        *) echo "$0 test [style|functional|unit|ci]"; exit;;
    esac
}

test_style() {
    echo "Running style checks"
    docker run \
        -v "${PWD}":/code \
        --rm "$C_PROJECT_NAME"-virtualenv-test:latest \
        flake8 --jobs=0 --config=test/style/.flake8 .
}

test_functional() {
    echo "Running functional tests"
    mkdir -p "tmp/coverage";

    docker-compose run \
        -v "${PWD}":/code \
        --rm test \
        py.test -p no:cacheprovider test/functional "$@"
}

test_unit() {
    echo "Running unit tests"
    mkdir -p "tmp/coverage";

    docker-compose run \
        -v "${PWD}":/code \
        --rm test \
        pytest -p no:cacheprovider test/unit "$@"
}

test_ci() {
    test_style

    coverage_clean

    local TEST_STATUS=0

    test_unit "$@" || TEST_STATUS=$?
    test_functional "$@" || TEST_STATUS=$?

    coverage_report
    exit $TEST_STATUS
}

docker_build() {
    docker build -t "$C_PROJECT_NAME"-virtualenv:latest -f build/virtualenv/Dockerfile build/virtualenv
    docker build -t "$C_PROJECT_NAME"-virtualenv-test:latest -f build/virtualenv/Dockerfile-test build/virtualenv
}

main "$@"
