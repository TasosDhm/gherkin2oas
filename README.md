## Introduction

The goal of the system is to assist developers in writing customer-friendly RESTful Web API functional requirements and also in documenting their API with the OpenAPI Specification.

The API Development process, using the proposed system, consists of two steps:
  1. Write resource files according to the Gherkin-Instructions.pdf document
  2. Run the Gherkin2OAS tool, which will in turn convert the Gherkin resource files to an OpenAPI Specification

## Installation

1. Clone or download
2. Navigate to the folder and install the required packages

```
pip install -r requirements.txt
```
3. Install textblob corpora:
```
python -m textblob.download_corpora
```
4. Install graphviz for your OS: https://www.graphviz.org/download/

5. Add graphviz to your PATH if you are on Windows (it's something like C:\Program Files(x86)\Graphviz\bin)

6. Install the swagger2openapi module:
```
npm install -g swagger2openapi
```

## Execution

1. Navigate to the src folder
2. Make sure you have at least one resource file written and the api_info.ini file filled. The api_info.ini file must be in the same folder with your resource files
3. Execute one of the following commands

  Normal execution
  ```
  python main.py -f /path/to/resources
  ```
  Execution with model from previous run (for speed gain)
  ```
  python main.py -m /path/to/model
  ``` 

  You can also specify the -fg flag to enable graph fixing mode.
  
  Use
  ```
  python main.py -h
  ```
  for help
  
## Notes

* The resource files must have '.resource' extension, can be organised in any number of folders and can co-exist with any number of other file types. The file names can have spaces, underscores or dashes.
* The reliability of the system is secured through following the Gherkin-Instructions.pdf document. Failure to follow the described rules will definitely lead to invalid OpenAPI Specification and sometimes unsuccessfull execution of the software tool.
* It is suggested to use the Sublime Text editor while writing the Gherkin resource files, with the following package https://github.com/waynemoore/sublime-gherkin-formatter

## Demo

You can view a demo of the system in the following video: https://www.youtube.com/watch?v=G5TNixy-dEc

