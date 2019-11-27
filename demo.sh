
#Title			: demo.sh
#Description	:
#Author			: pmorvalho
#Date			: 2019/10/22
#version		:
#Usage			: ./demo.sh input-file.in/-d [-r]
#Notes			: select an input file from the textbook folder or use -d for demo, -r prints also the R query
#==============================================================================

printRsol="-nr"
queryMessage="Discovering SQL query...
"
if [ "$2" == "-r" ];
then
  printRsol=""
  queryMessage="Discovering R and SQL queries...
  "
fi

echo
if [ $1 != "-d" ]
then
  echo "Inputs:
  "
  for i in tests-examples/textbook/tables/$1-*;
  do
  cat $i
  echo ""
  read -p ""
  done

  echo "Output:
  "
  cat tests-examples/textbook/tables/$1.out
  echo ""
  read -p ""


  echo $queryMessage
  time python3 squaresEnumerator.py $printRsol tests-examples/textbook/$1.in 2> output.err
  # test order # 13 # 7 # 8 # 5 # 1 # 21
else
  echo "Inputs:
  "
  for i in tests-examples/demo/tables/*.txt;
  do
  cat $i
  echo ""
  read -p ""
  done

  echo "Output:
  "
  cat tests-examples/demo/tables/demo.out
  echo ""
  read -p ""

  echo $queryMessage
  time python3 squaresEnumerator.py $printRsol tests-examples/demo/demo.in 2> output.err
fi
