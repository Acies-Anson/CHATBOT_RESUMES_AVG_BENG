PDF2CSV

    -----> data 
            -----> Given data
            -----> Extracted_json
            -----> Extracted_text

    -----> tessaract (old code using tessar)
            -----> pdf2text.py (using tessaract)
            -----> text2json.py (using headings)

    -----> testing 
            -----> test_count.py (Compare folder in data to see which is missing from the files converted)
            -----> text2json_failedfiles (Reruning the text to json conversion for the failed files and found Python Developer/ 74.txt had been generated with different language)

    ------> scripts
            -----> pdf2text.py
            -----> text2json.py
            -----> json2csv.py
            ..............................................................................................