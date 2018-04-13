
# Sublime Text Plugin for `panbuild`

This plugin makes it possible to use [`panbuild`][panbuild] --a _make-like_ builder for [pandoc][pandoc]-- within the [Sublime Text](https://www.sublimetext.com/) editor. Essentially, the plugin removes the need to type `panbuild` or `pandoc` commands from a terminal window; all the interaction with `panbuild` and `pandoc` takes place from the graphical user interface of Sublime Text. 

[panbuild]: https://github.com/jcsaezal/panbuild
[pandoc]: http://pandoc.org/


## Installation

The plugin is compatible with both Sublime Text 2 and 3.

At the moment, only a _beta_ version of the plugin exists, which is not yet available at [Package Control](https://packagecontrol.io/). To install the plugin, you must proceed as follows:

1. Download the [ZIPped version](https://github.com/jcsaezal/SublimeText-Panbuild/archive/master.zip) of the plugin's repository and extract it on your computer
2. Rename the `SublimeText-Panbuild-master` folder -created as a result of extracting the ZIP file- as `Panbuild`
3. Open Sublime Text's plugin folder (Go to menu entry `Preferences -> Browse Packages...` within Sublime Text). Then, drag and drop the freshly renamed `Panbuild` folder there. That will get the plugin installed. 

## Usage

Before using the plugin, make sure you create a `build.yaml` file in the same folder where the source code of your document is located -what serves as input to `pandoc` (e.g., Markdown files)-. The `build.yaml` file should contain the rules for building the document, which basically define the pandoc commands that will be used to generate particular output files -in one of the target formats supported by `pandoc` (PDF, DOCX, EPUB, etc.)- from the source code of your document. For more information on the syntax and structure of `build.yaml` files, please check out the `panbuild`'s documentation available [here](https://github.com/jcsaezal/panbuild).

Once the `build.yaml` file has been created, enable the "Panbuild" build system by clicking on the following menu entry: `Tools -> Build System -> Panbuild`


![missing screenshot](https://raw.githubusercontent.com/jcsaezal/SublimeText-Panbuild/master/images/select-panbuild.png)


To tell `pandoc` to transform your document into one of the output formats defined in the `build.yaml` file, just type `CTRL`+ `B` (On Windows or Linux), or `CMD`+`B` (on Mac OS). In doing so,  a list with the available output formats will be displayed as in the figure below:

![missing screenshot](https://raw.githubusercontent.com/jcsaezal/SublimeText-Panbuild/master/images/example-formats.png)

Clicking on the desired format's list entry will initiate the build process with `pandoc`. When done, the document will be automatically opened with the default application for viewing that kind of file.


