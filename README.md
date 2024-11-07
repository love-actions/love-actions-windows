# love-actions-windows

## Which version to use?

- For the `11.5` version of the [LÖVE](https://love2d.org/) framework, use the `v2` tag or `v2.x.x` tags.
- For the `11.4` version of the [LÖVE](https://love2d.org/) framework, use the `v1` tag or `v1.x.x` tags.

### Branches

This branch is for the latest release version of the [LÖVE](https://love2d.org/) framework.

For the `11.4` version, please refer to the [**11.4**](https://github.com/love-actions/love-actions-windows/tree/11.4) branch.

## About

Github Action for building & deploying Windows `.zip` packages and `.exe` installer of a [LÖVE](https://love2d.org/) framework based game.

### Related actions

See related actions below:

[Love actions bare package](https://github.com/marketplace/actions/love-actions-bare-package)

[Love actions for testing](https://github.com/marketplace/actions/love-actions-for-testing)

## Quick example

```yaml
- name: Build Windows packages
  id: build-packages
  uses: love-action/love-actions-windows@v1
  with:
    love-package: ./game.love
    icon-path: ./assets/windows/icon.ico
    rc-path: ./assets/windows/template.rc
    product-name: love_app
    app-id: ${{ secrets.APP_ID }}
    product-website: https://www.example.com
    installer-languages: English.isl ChineseSimplified.isl
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
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      - name: Build core love package
        uses: love-actions/love-actions-core@v1
        with:
          build-list: ./media/ ./parts/ ./Zframework/ ./conf.lua ./main.lua ./version.lua
          package-path: ${{ env.CORE_LOVE_PACKAGE_PATH }}
      - name: Upload core love package
        uses: actions/upload-artifact@v4
        with:
          name: ${{ env.CORE_LOVE_ARTIFACT_NAME }}
          path: ${{ env.CORE_LOVE_PACKAGE_PATH }}
  auto-test:
    runs-on: ubuntu-latest
    needs: build-core
    steps:
      - uses: actions/checkout@v4
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
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      # Download your core love package here
      - name: Download core love package
        uses: actions/download-artifact@v4
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
          love-package: ${{ env.CORE_LOVE_PACKAGE_PATH }}
          icon-path: ./.github/build/windows/${{ env.BUILD_TYPE }}/icon.ico
          rc-path: ./.github/build/windows/${{ env.BUILD_TYPE }}/template.rc
          extra-assets-x86: ./ColdClear/x86/CCloader.dll ./ColdClear/x86/cold_clear.dll
          extra-assets-x64: ./ColdClear/x64/CCloader.dll ./ColdClear/x64/cold_clear.dll
          product-name: ${{ env.PRODUCT_NAME }}
          app-id: ${{ secrets.APP_ID }}
          project-website: https://www.example.com/
          installer-languages: English.isl ChineseSimplified.isl Japanese.isl French.isl
          output-folder: ${{ env.OUTPUT_FOLDER }}
      - name: Upload 32-bit artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ needs.get-info.outputs.base-name }}_Windows_x86
          path: ${{ env.OUTPUT_FOLDER }}/${{ env.PRODUCT_NAME }}_x86.zip
      - name: Upload 64-bit artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ needs.get-info.outputs.base-name }}_Windows_x64
          path: ${{ env.OUTPUT_FOLDER }}/${{ env.PRODUCT_NAME }}_x64.zip
      - name: Upload installer artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ needs.get-info.outputs.base-name }}_Windows_installer
          path: ${{ env.OUTPUT_FOLDER }}/${{ env.PRODUCT_NAME }}_installer.exe
```

## All inputs

| Name                  | Required | Default                  | Description                                                                                                                     |
| --------------------- | -------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `love-ref`            | `false`  | `"11.5"`                 | `love` release ref. Could only be release tags like `11.5`                                                                      |
| `love-package`        | `false`  | `"./game.love"`          | Love package. Used to assemble the executable.                                                                                  |
| `icon-path`           | `false`  | `""`                     | Path to the exe's icon. If not specified, the product has no icon.                                                              |
| `rc-path`             | `false`  | `""`                     | Path to the `.rc` file. Used to configure the properties of the product.                                                        |
| `extra-assets-x86`    | `false`  | `""`                     | List of folder & file paths to be added to x86 product folder.                                                                  |
| `extra-assets-x64`    | `false`  | `""`                     | List of folder & file paths to be added to x64 product folder.                                                                  |
| `product-name`        | `false`  | `"love_app"`             | Base name of the package.                                                                                                       |
| `app-id`              | `false`  | `""`                     | The application identifier (uuid) for the installer. You need to download inno setup and use the built-in tool to generate one. |
| `project-website`     | `false`  | `""`                     | The project's homepage url.                                                                                                     |
| `installer-languages` | `false`  | `English.isl`            | List of languages supported by the installer. You can find references [here](https://jrsoftware.org/files/istrans/)             |
| `output-folder`       | `false`  | `"./build"`              | Packages output folder. All packages would be placed here.                                                                      |
| `love-actions-folder` | `false`  | `"love-actions-windows"` | Path to the `love-actions-windows` folder. Would be used to run all the action steps                                            |

## All outputs

| Name            | Example                                                                            | Description                                                                                      |
| --------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `package-paths` | `./build/love_app_x86.zip ./build/love_app_x64.zip ./build/love_app_installer.exe` | Built packages' paths in a bash-style list relative to the repository root, separated by spaces. |

## Other platforms

If you need to build game for other platforms, please check links below:

[Love actions for android](https://github.com/marketplace/actions/love-actions-for-android)

[Love actions for iOS](https://github.com/marketplace/actions/love-actions-for-ios)

[Love actions for Linux](https://github.com/marketplace/actions/love-actions-for-linux)

[Love actions for macOS portable](https://github.com/marketplace/actions/love-actions-for-macos-portable)

[Love actions for macOS AppStore](https://github.com/marketplace/actions/love-actions-for-macos-appstore)
