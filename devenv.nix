{ pkgs, ... }:

{
  # Java 17 for building and testing the Android TV launcher
  languages.java = {
    enable = true;
    jdk.package = pkgs.temurin-bin-17;
  };

  # Python 3.12 with uv for running tooling, safety scripts, and tests
  languages.python = {
    enable = true;
    package = pkgs.python312;
    uv.enable = true;
  };

  # CLI utilities and Android debug bridge tools
  packages = with pkgs; [
    android-tools
    eza
    fd
    jq
    ripgrep
    sd
    uv
  ];

  # Prepare tools virtualenv automatically when entering the shell
  enterShell = ''
    if [ ! -d tools/venv ]; then
      echo "Creating Python virtualenv in tools/venv..."
      uv venv tools/venv
    fi
    uv pip install -q -r tools/requirements.txt --python tools/venv/bin/python
  '';

  # Handy shortcuts for common tasks
  scripts = {
    test-tools.exec = "python3 -m unittest discover -s tests -v";
    build-launcher.exec = "cd launcher && ./gradlew assembleRelease";
    test-launcher.exec = "cd launcher && ./gradlew testReleaseUnitTest lintRelease";
    probe-tv.exec = "tools/tv.py --probe";
    verify-closed-port.exec = "tools/adb-closed.py \"$@\"";
  };
}
