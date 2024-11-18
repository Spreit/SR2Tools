# Sega Rally 2 File Formats

### Textures

|      Signature      | File Formats        | Description                                                |
| :-----------------: | ------------------- | ---------------------------------------------------------- |
| [RHBG](#RHBGFormat) | .bg                 | Loading and Game Over Yeaaah screens                       |
| [RTEX](#RTEXFormat) | .txr .sky .sea .tyk | Most common texture type                                   |
| [MTEX](#MTEXFormat) | .txr                | US/EU Dreamcast stage textures with weird tile compression |
| [RTXR](#RTXRFormat) | .txr                | Used in a few textures on Dreamcast                        |

### 3D

| Signature | File Formats       | Description        |
| --------- | ------------------ | ------------------ |
| None      | [.mdl](#MDLFormat) | Used for 3D models |

### Other

| Signature           | File Formats | Description                                                                   |
| ------------------- | ------------ | ----------------------------------------------------------------------------- |
| [SARC](#SARCFormat) | .bin         | Uncompressed archive consisting of several files. Used for cars on Dreamcast. |
| None                | .dat         | Stage data                                                                    |

<a name="RHBGFormat"></a>
## RHBG Format Structure

|             |                         | Size                    |
| ----------- | ----------------------- | ----------------------- |
| Header      |                         | 16 bytes                |
|             | File Signature (RHBG)   | 4 bytes                 |
|             | Texture Width           | 4 bytes                 |
|             | Texture Height          | 4 bytes                 |
|             | Texture Size (in bytes) | 4 bytes                 |
| Pixel Bytes | RGB565 color format     | Texture Size (in bytes) |

<a name="RTEXFormat"></a>
## RTEX Format Structure

|             |                         | Size                                                        |
| ----------- | ----------------------- | ----------------------------------------------------------- |
| Header      |                         | 4096 bytes                                                  |
|             | File Header             | 16 bytes                                                    |
|             | Sub-Texture Headers     | 16 bytes, Texture Count times                               |
|             | Palettes                | 1024 bytes, Palette Count times                             |
|             | Padding                 | Until total size reaches 4096 bytes                         |
| Pixel Bytes |                         | Sum of all sub-texture sizes                                |
|             | Sub-Texture Pixel Bytes | Sub-texture size (in bytes), <br>from a correspoding header |

## Header

Total Size - 4096 bytes

### File Header

Total size - 16 bytes

| Offset | Size (in bytes) | Description             |
| :----: | :-------------: | ----------------------- |
|  0x0   |        4        | File Signature (RTEX)   |
|  0x3   |        4        | Texture Count           |
|  0x7   |        4        | Palette Count (Up to 3) |
|  0xA   |        4        | Palette Order           |

Palette Order

| Byte Values |                                                                 |
| :---------: | --------------------------------------------------------------- |
| 00 00 00 00 | if one or no palette is present                                 |
| 01 02 00 00 | if two palettes are present                                     |
| 01 02 03 00 | if three palettes are present                                   |
|             | fourth palette doesn't fit into the header, so it can't be used |

---

## Sub-Texture Headers

Total Size - 16 bytes \* Texture Count

| Offset | Size (in bytes) | Description                              |
| :----: | :-------------: | ---------------------------------------- |
|  0x0   |        1        | Color Format                             |
|  0x1   |        1        | Palette usage                            |
|  0x2   |        2        | No idea, doesn't seem to affect anything |
|  0x4   |        4        | Width and height (square texture)        |
|  0x8   |        4        | Sub-texture size (in bytes)              |
|  0xC   |        4        | Index of used palette                    |

---

| Color format | Value |
| ------------ | :---: |
| RGB565       |  00   |
| ARGB1555     |  02   |
| Unknown      |  04   |
| Unknown      |  06   |
| ARGB4444     |  08   |

| Palette usage | Value |
| ------------- | :---: |
| Not used      |  00   |
| Used          |  04   |

| No Idea | Value |
| ------- | :---: |
| ???     | 00 00 |
| ???     | 00 40 |
| ???     | 00 50 |
| ???     | 00 80 |
| ???     | 00 90 |

| Palette Index                | Value |
| ---------------------------- | :---: |
| No palette used              |  00   |
| First palette                |  01   |
| Second palette               |  02   |
| Third palette                |  03   |
| Fourth palette can't be used |       |

---

## Palettes

Total size: 1024 bytes \* Palette Count

Each palette contains 256 colors in RGBX8888 format

### Padding until the header size reaches 4096 bytes

---

## Pixel Bytes

Total size: Sum of all sub-texture sizes

Sub-Texture Pixel Bytes

---

<a name="RTXRFormat"></a>
## RTXR Format Structure
Used in like 0.5 textures in dreamcast versions (taco.txr and menu car textures)

Unlike RTEX, stores pairs of Header + Pixel Bytes one after another.

_Look into further_

---

<a name="MTEXFormat"></a>
## MTEX Format Structure

Tile-based textures, may include additional compression.

Used for track textures in EU/US Dreamcast ports to reduce loading time.

|             |                         | Size                                                        |
| ----------- | ----------------------- | ----------------------------------------------------------- |
| Header      |                         | 4096 bytes                                                  |
|             | File Header             | 16 bytes                                                    |
|             | Sub-Texture Headers     | 16 bytes, Texture Count times                               |
|             | Palettes                | 1024 bytes, Palette Count times                             |
|             | Padding                 | Until total size reaches 4096 bytes                         |
| Pixel Bytes |                         | Sum of all sub-texture sizes                                |
|             | Sub-Texture Pixel Bytes | Sub-texture size (in bytes), <br>from a correspoding header |

Header

File Header

| Offset | Size (in bytes) | Description           |
| ------ | --------------- | --------------------- |
| 0x0    | 4               | File Signature (MTEX) |
| 0x3    | 4               | Texture Count         |
| 0x7    | 8               | Padding               |

Texture Headers

Total Size - 16 bytes \* Texture Count

| Offset | Size (in bytes) | Description                       |
| :----: | :-------------: | --------------------------------- |
|  0x0   |        4        | No Idea + Color Format            |
|  0x3   |        2        | Additional Compression            |
|  0x4   |        4        | Width and height (square texture) |
|  0x8   |        4        | Offset to Pixel Bytes             |
|  0xC   |        4        | Sub-texture Pixel Bytes size      |

---

| Color Format | Value |
| ------------ | :---: |
| RGB565       |  X0   |
| ARGB1555     |  X2   |
| Unknown      |  X4   |
| Unknown      |  X6   |
| ARGB4444     |  X8   |

MTEX merged Color Format and No Idea form RTEX to one byte

| Additional Compression | Value |
| ---------------------- | :---: |
| Not used               | 00 00 |
| Used                   | 01 00 |

| No Idea | Value |
| ------- | :---: |
| ???     | 00 00 |
| ???     | 00 40 |
| ???     | 00 50 |
| ???     | 00 80 |
| ???     | 00 90 |

### Pixel Bytes

MTEX textures are tile based. Image is split up into 256 2x2 tiles and index array.

| Size (in bytes)         | Description          |
| ----------------------- | -------------------- |
| 2048                    | 256 2x2 16 bit Tiles |
| Sub-texture size - 2048 | Tile Indexes         |

Index array is not stored linearly as you would expect, but needs to be unpacked recursively like this:

|     |     |
| --- | --- |
| 1   | 3   |
| 2   | 4   |

If additional compression is used, then sub-texture's pixel bytes are split into: mini header with compressed and uncompressed size and compressed bytes (most likely both tiles and indexes). Compression algorithm is unknown.

---

<a name="MDLFormat"></a>
## 3D models

Documented in blender import script

---

<a name="SARCFormat"></a>
## SARC Archive

Simply several files stitched together with some additional info

### File Header

Size - 8 bytes

| Size (in bytes) | Description           |
| --------------- | --------------------- |
| 4               | File Signature (SARC) |
| 4               | File Count            |

---

### Packed Files Header

Size - 272 bytes, File Count times

| Size (in bytes) | Description                                                |
| --------------- | ---------------------------------------------------------- |
| 4               | Padding                                                    |
| 4               | File Size                                                  |
| 4               | File Size (again, might be different)                      |
| 4               | Offset to file bytes                                       |
| 256             | File Path, probably used by WinCE, so shouldn't be changed |

File Path includes japanese characters and uses "cp932" encoding, at least that one works.

---

File Bytes in the order of their headers
