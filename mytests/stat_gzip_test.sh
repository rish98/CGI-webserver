curl -H "Accept-Encoding: gzip" "localhost:8072/home.js"|gunzip >temp

if diff temp stat_gzip_test_exp > /dev/null
then
    echo "Files matches expected result"
else
    echo "File does not match expected result"
fi
