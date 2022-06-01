curl "localhost:8072/stat_html_test.html">temp

if diff temp stat_html_test_exp > /dev/null
then
    echo "Files matches expected result"
else
    echo "File does not match expected result"
fi
