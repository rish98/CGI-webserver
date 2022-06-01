curl "localhost:8072/stat_plain_test.txt" -i>temp

if diff temp stat_plain_test_exp > /dev/null
then
    echo "Files matches expected result"
else
    echo "File does not match expected result"
fi
