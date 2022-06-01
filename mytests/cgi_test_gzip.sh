curl -H "Accept-Encoding: gzip" "localhost:8072/cgibin/cgi_test_gzip.py" --output - |gunzip >temp

if diff temp cgi_test_gzip_exp > /dev/null
then
    echo "Files matches expected result"
else
    echo "File does not match expected result"
fi
