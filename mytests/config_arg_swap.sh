# python webserv.py config_arg_swap.cfg > ./mytests/temp
# run above line on a terminal and then run this bash script please

if diff temp config_arg_swap_exp > /dev/null
then
    echo "Files matches expected result"
else
    echo "File does not match expected result"
fi
