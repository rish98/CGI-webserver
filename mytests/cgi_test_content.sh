curl "localhost:8072/cgibin/cgi_test_content.py" -i >temp
if diff temp cgi_test_content_exp > /dev/null
then
    echo "Files matches expected result"
else
    echo "File does not match expected result"
fi
