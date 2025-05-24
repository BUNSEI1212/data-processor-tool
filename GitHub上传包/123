name: Build Mac App

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-mac:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install PyInstaller Pillow matplotlib
    
    - name: Build App
      run: |
        pyinstaller --onedir --windowed --name="数据处理工具" \
          --icon="app_icon.png" \
          --add-data="app_icon.png:." \
          --osx-bundle-identifier="com.dataprocessor.tool" \
          代码.py
    
    - name: Create DMG
      run: |
        # 创建DMG
        hdiutil create -size 200m -fs HFS+ -volname "数据处理工具" temp.dmg
        hdiutil attach temp.dmg
        cp -R "dist/数据处理工具.app" "/Volumes/数据处理工具/"
        ln -s /Applications "/Volumes/数据处理工具/Applications"
        hdiutil detach "/Volumes/数据处理工具"
        hdiutil convert temp.dmg -format UDZO -o "数据处理工具_Mac版.dmg"
        rm temp.dmg
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: mac-app
        path: |
          数据处理工具_Mac版.dmg
          dist/数据处理工具.app 
