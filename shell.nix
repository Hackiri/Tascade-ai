{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python dependencies
    python3
    python3Packages.pip
    python3Packages.numpy
    python3Packages.pandas
    python3Packages.matplotlib
    python3Packages.seaborn
    python3Packages.networkx
    python3Packages.flask
    python3Packages.flask-cors
    python3Packages.pyjwt
    python3Packages.tabulate
    python3Packages.pyyaml
    python3Packages.beautifulsoup4
    python3Packages.markdown
    
    # Node.js dependencies for npm publishing
    nodejs_22
    nodePackages.npm
  ];

  shellHook = ''
    echo "Entering Tascade AI development environment"
    # Create a temporary Python environment
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    # Set up npm environment
    mkdir -p ./.npm-global
    export NPM_CONFIG_PREFIX=$PWD/.npm-global
    export PATH=$NPM_CONFIG_PREFIX/bin:$PATH
    
    echo "Node.js $(node -v) and npm $(npm -v) are available"
    echo "Use 'npm link' to test the package locally"
  '';
}
