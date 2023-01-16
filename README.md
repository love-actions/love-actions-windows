# love-actions-windows

## About

Github Action for building & deploying Linux `.AppImage` packages of a [LÖVE](https://love2d.org/) framework based game.

### Related actions

See related actions below:

[Love actions bare package](https://github.com/marketplace/actions/love-actions-bare-package)

[Love actions for testing](https://github.com/marketplace/actions/love-actions-for-testing)

[Love actions for android](https://github.com/marketplace/actions/love-actions-for-android)

[Love actions for iOS](https://github.com/marketplace/actions/love-actions-for-ios)

[Love actions for Linux](https://github.com/marketplace/actions/love-actions-for-linux)

[Love actions for macOS portable](https://github.com/marketplace/actions/love-actions-for-macos-portable)

[Love actions for macOS AppStore](https://github.com/marketplace/actions/love-actions-for-macos-appstore)

## Quick example

```yaml
- name: Build Windows packages
  id: build-packages
  uses: love-action/love-actions-windows@v1
  with:
    icon-path: ./assets/windows/icon.ico
    rc-path: ./assets/windows/template.rc
    love-package: ./game.love
    product-name: love_app
    version-string: "2.3.4"
    output-folder: "./dist"
```

## With [Love actions bare package](https://github.com/marketplace/actions/love-actions-bare-package) and [Love actions for testing](https://github.com/marketplace/actions/love-actions-for-testing)

```yml
env:
  BUILD_TYPE: ${{ fromJSON('["dev", "release"]')[startsWith(github.ref, 'refs/tags/v')] }}
  CORE_LOVE_PACKAGE_PATH: ./core.love
  CORE_LOVE_ARTIFACT_NAME: core_love_package
  PRODUCT_NAME: my_love_app
  BUNDLE_ID: com.example.myloveapp

jobs:
  build-core:
    runs-on: ubuntu-latest
    env:
      OUTPUT_FOLDER: ./build
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive
      - name: Build core love package
        uses: love-actions/love-actions-core@v1
        with:
          build-list: ./media/ ./parts/ ./Zframework/ ./conf.lua ./main.lua ./version.lua
          package-path: ${{ env.CORE_LOVE_PACKAGE_PATH }}
      - name: Upload core love package
        uses: actions/upload-artifact@v3
        with:
          name: ${{ env.CORE_LOVE_ARTIFACT_NAME }}
          path: ${{ env.CORE_LOVE_PACKAGE_PATH }}
  auto-test:
    runs-on: ubuntu-latest
    needs: build-core
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive
      - name: Love actions for testing
        uses: love-actions/love-actions-test@v1
        with:
          font-path: ./parts/fonts/proportional.otf
          language-folder: ./parts/language
  build-windows:
    runs-on: windows-latest
    needs: [build-core, auto-test]
    env:
      OUTPUT_FOLDER: ./build
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive
      # Download your core love package here
      - name: Download core love package
        uses: actions/download-artifact@v3
        with:
          name: ${{ env.CORE_LOVE_ARTIFACT_NAME }}
      # This is an example dynamic library
      - name: Download ColdClear
        uses: ./.github/actions/get-cc
        with:
          platform: Windows
          dir: ./ColdClear
      - name: Build Windows packages
        id: build-packages
        uses: love-actions/love-actions-windows@v1
        with:
          icon-path: ./.github/build/windows/${{ env.BUILD_TYPE }}/icon.ico
          rc-path: ./.github/build/windows/${{ env.BUILD_TYPE }}/template.rc
          love-package: ${{ env.CORE_LOVE_PACKAGE_PATH }}
          extra-assets-x86: ./ColdClear/x86/CCloader.dll ./ColdClear/x86/cold_clear.dll
          extra-assets-x64: ./ColdClear/x64/CCloader.dll ./ColdClear/x64/cold_clear.dll
          product-name: ${{ env.PRODUCT_NAME }}
          version-string: "1.0.0"
          output-folder: ${{ env.OUTPUT_FOLDER }}
      - name: Upload 32-bit artifact
        uses: actions/upload-artifact@v3
        with:
          name: ${{ needs.get-info.outputs.base-name }}_Windows_x86
          path: ${{ env.OUTPUT_FOLDER }}/${{ env.PRODUCT_NAME }}_x86.zip
      - name: Upload 64-bit artifact
        uses: actions/upload-artifact@v3
        with:
          name: ${{ needs.get-info.outputs.base-name }}_Windows_x64
          path: ${{ env.OUTPUT_FOLDER }}/${{ env.PRODUCT_NAME }}_x64.zip
```

## All inputs

| Name               | Required  | Default           | Description                                                     |
| :----------------- | --------- | ----------------- | --------------------------------------------------------------- |
| `icon-path`      | `false` | `"./icon.ico"`  | Path to the exe's icon. Use LÖVE default if not specified      |
| `rc-path`        | `true`  | `""`            | Path to the `.rc` file. Used to compile exe's resource file   |
| `love-package`   | `false` | `"./game.love"` | Path to the appImage's icon. Use LÖVE default if not specified |
| `product-name`   | `false` | `"love_app"`    | Love package. Used to assemble the executable                   |
| `version-string` | `false` | `"11.4"`        | Base name of the package. Used to rename products               |
| `output-folder`  | `false` | `"./build"`     | Packages output folder. All packages would be placed here       |

## All outputs

| Name              | Example                                               | Description                                                                                     |
| :---------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `package-paths` | `./build/love_app_x86.zip ./build/love_app_x64.zip` | Built packages' paths in a bash-style list relative to the repository root, separated by spaces |
