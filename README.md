
# Sublime Text Plugin for `panbuild`

This plugin makes it possible to use [`panbuild`][panbuild] --a _make-like_ builder for [pandoc][pandoc]-- within the [Sublime Text](https://www.sublimetext.com/) editor. Essentially, the plugin removes the need to type `panbuild` or `pandoc` commands from a terminal window; all the interaction with `panbuild` and `pandoc` (used underneath) can performed from the graphical user interface of Sublime Text. 

[panbuild]: https://github.com/jcsaezal/panbuild

## Installation

The plugin is compatible with both Sublime Text 2 and 3.

At the moment, only a _beta_ version of the plugin exists, which is not yet available at [Package Control](https://packagecontrol.io/). To install the plugin, you must proceed as follows:

1. Download the [ZIPped version](https://github.com/jcsaezal/SublimeText-Panbuild/archive/master.zip) of this repository and extract it on your computer
2. Rename the `SublimeText-Panbuild-master` folder, which shows up when extracting the ZIP file, as `Panbuild`
3. Open Sublime Text's plugin folder (Go to menu entry `Prefereces -> Browse Packages...` within Sublime Text) and drag and drop the freshly renamed `Panbuild` folder there. That will get the plugin installed. 

## Usage

Before using the plugin, make sure you create a `build.yaml` file in the same folder with the source code of your document --what serves as input to `pandoc` (e.g., Markdown files)--. The `build.yaml` file should contain the rules for building the document, which basically define the pandoc command that will be used to build a particular output file --in one of the target formats supported by `pandoc` (PDF, DOCX, EPUB, etc.)-- from the source code of your document. For more information on the syntax and structure of `build.yaml` files, please check out the `panbuild`'s documentation available [here](https://github.com/jcsaezal/panbuild).

Once the `build.yaml` file has been created, enable "Panbuild" build system by clicking on the following menu entry: `Tools -> Build System -> Panbuild`


![missing screenshot](https://raw.githubusercontent.com/jcsaezal/SublimeText-Panbuild/master/images/select-panbuild.png)


To tell `pandoc` to transform your document into one of the output formats defined in the `build.yaml` file, just type `CTRL`+ `B` (On Windows or Linux), or `CMD`+`B` (on Mac OS). That will display a list of the available output formats, such as in the figure below:

![missing screenshot](https://raw.githubusercontent.com/jcsaezal/SublimeText-Panbuild/master/images/example-formats.png)

Clicking on the desired one will initate the build process with `pandoc`. When done, the document will be  automatically displayed (with the default application to open that kind of file).


