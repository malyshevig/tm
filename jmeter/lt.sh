


export JMETER=/home/ilia/local/apache-jmeter-5.6.3/bin/jmeter


# Full command for production load test
$JMETER -n \
  -t ./lt1.jmx \
  -l ./results/test_$(date +%Y%m%d_%H%M%S).jtl \
  -e -o ./reports/test_$(date +%Y%m%d_%H%M%S) \
  -Jtasks=500000 \
  -Jworkers=5000 \
  -Jcycles=100 \
  -Jhost=localhost \
  -Jport=81 \
