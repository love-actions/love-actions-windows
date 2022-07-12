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

[Love actions for macOS](https://github.com/marketplace/actions/love-actions-for-macos)

## Quick example

```yaml
- name: Build Windows packages
  id: build-packages
  uses: 26F-Studio/love-actions-windows@main
  with:
    icon-path: ./assets/windows/icon.ico
    rc-path: ./assets/windows/template.rc
    love-package: ./game.love
    product-name: love_app
    version-string: "2.3.4"
    output-folder: "./dist"
```

## All inputs

| Name             | Required | Default         | Description                                                  |
| :--------------- | -------- | --------------- | ------------------------------------------------------------ |
| `icon-path`      | `false`  | `"./icon.ico"`  | Path to the exe's icon. Use LÖVE default if not specified |
| `rc-path`        | `true`   | `""`            | Path to the `.rc` file. Used to compile exe's resource file |
| `love-package`   | `false`  | `"./game.love"` | Path to the appImage's icon. Use LÖVE default if not specified |
| `product-name`   | `false`  | `"love_app"`    | Love package. Used to assemble the executable              |
| `version-string` | `false`  | `"11.4"`        | Base name of the package. Used to rename products          |
| `output-folder`  | `false`  | `"./build"`     | Packages output folder. All packages would be placed here   |

## All outputs

| Name            | Example                                             | Description                                                  |
| :-------------- | --------------------------------------------------- | ------------------------------------------------------------ |
| `package-paths` | `./build/love_app_x86.zip ./build/love_app_x64.zip` | Built packages' paths in a bash-style list relative to the repository root, separated by spaces |
