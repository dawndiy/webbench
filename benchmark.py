#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys, getopt, urllib2, urlparse, time, threading

###GLOBALS###

server_soft = ''
server_port = 80
host_url = 'http://localhost/'
host_name = 'localhost'

doc_path = '/'
doc_length = 0

request_num = 1
concurrency_num = 1

request_completed_num = 0
request_failed_num = 0
request_per_second = 0
time_taken = 0

html_transferred = 0



request_time = []
percs = [50, 66, 75, 80, 90, 95, 98, 99, 100]


def usage():
    '''display the usage'''
    
    print(
        'Usage: ab [options] [http[s]://]hostname[:port]/path\n'
        'Options are:\n'
        '    -n requests     Number of requests to perform\n'
        '    -c concurrency  Number of multiple requests to make\n'
        '    -h help         Display usage information (this message)\n'
    )
    exit()


def get_options(argv):
    '''get all options and values'''
    global concurrency_num, request_num
    
    try:
        opts, args = getopt.getopt(argv[1:], "n:c:h", ["requests=", "concurrency=", "help"])
        
        # get all options    
        for opt, arg in opts:
            if opt in ['-n', '--request']:
                request_num = int(arg)
            if opt in ['-c', '--concurrency']:
                concurrency_num = int(arg)
            if opt in ['-h', '--help']:
                usage()
        
        
    except (getopt.GetoptError, ValueError), e:
        print(e)
        usage()
    ''' check values '''
    if request_num < 1 or concurrency_num < 1:
        print('Invalid number')
        usage()
    if request_num < concurrency_num:
        print('Cannot use concurrency level greater than total number of requests')
        usage()
        
    return args


def get_server_info(host_url):
    '''get server information'''
    global server_soft, host_name, server_port, doc_length
    # format host url like 'http://www.example.com'
    url_parse = urlparse.urlparse(host_url, 'http')
    host_url = url_parse.scheme + '://' + url_parse.netloc + url_parse.path
    
    # get server port
    try:
        server_port = int(host_url.split(':')[2].split('/')[0])
    except IndexError:
        server_port = 80
        
    ''' get server info '''
    try:
        host = urllib2.urlopen(host_url)    # 404
    except urllib2.URLERROR, e:
        print(e)
        usage()
    try:
        # get server software
        server_soft = host.info()['server']  
    except KeyError:
        server_soft = 'UNKOWN'
    try:    
        # get document length
        doc_length = host.info()['content-length']
    except KeyError, e:
        doc_length = sys.getsizeof(host.read())
    
    # get document path and hostname
    host_url = host.geturl()
    url_parse = urlparse.urlparse(host_url)
    doc_path = url_parse.path if url_parse.path != '' else '/'
    host_name = url_parse.netloc.split(':')[0]  # remove port

def do_request(url):
    '''do request'''
    global request_completed_num, request_failed_num, html_transferred, request_time
    
    try:
        start_req = time.time()
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        finish_req = time.time()
        
        # get time each request taken
        request_time.append(finish_req - start_req) 
        
        request_completed_num +=1
        if response.getcode() == 200:
            response_size = sys.getsizeof(response.read())
            html_transferred += response_size            
        else:
            request_failed_num += 1
    except urllib2.URLError, e:
        print('URLError')
        usage()

def result():
    '''display the test result'''
    print('Server Software:        %s' % server_soft)
    print('Server Hostname:        %s' % host_name)
    print('Server Port:            %d' % server_port)
    print('')
    print('Document Path:          %s' % doc_path)
    print('Document Length:        %s bytes' % doc_length)
    print('')
    print('Concurrency Level:      %d' % concurrency_num)
    print('Time taken for tests:   %f seconds' % time_taken)
    print('Complete requests:      %d' % request_completed_num)
    print('Failed requests:        %d' % request_failed_num)
    print('HTML transferred:       %d bytes' % html_transferred) 
    print('Requests per second:    %.2f [#/sec] (mean)' % (request_completed_num / time_taken))
    print('Time per request:       %.3f [ms] (mean)' % (concurrency_num * time_taken * 1000 / request_completed_num))
    print('Time per request:       %.3f [ms] (mean, across all concurrent requests)' % (time_taken * 1000 / request_completed_num))
    print('Transfer rate:          %.2f [Kbytes/sec] received' % (html_transferred / 1024 / time_taken))
    print('')
    print('Percentage of the requests served within a certain time (ms)')
    request_time.sort()
    for i in percs:
        if i <= 0:
            print(' 0%%  <0> (never)') 
        elif i >= 100:
            print(' 100%%  %d (longest request)' % (request_time[-1]*1000))
        else:
            print('  %d%%  %d' % (i, request_time[int(request_completed_num * i / 100)] * 1000))
 


def main(argv):
    '''MAIN'''
    
    global time_taken
    
    # start time    
    start_time = time.time()
    
    args = get_options(argv)
            
    try:
        # get host url
        host_url = args[0]
    except IndexError, e:
        print(e)
        usage()    
    print('Benchmarking ' + host_url + ' (be patient).....')
    get_server_info(host_url)
    
    ''' test requests '''
    test_num = request_num / concurrency_num
    threads = []
    for i in range(test_num):

        for c in range(concurrency_num):
            t = threading.Thread(target=do_request, args=(host_url,))
            threads.append(t)
        
        for c in range(concurrency_num):
            threads[c].start()
            
        for c in range(concurrency_num):
            threads[c].join()
             
        threads = []
        
    test_num_left = request_num % concurrency_num
    if test_num_left != 0:
        threads_left = []
        for l in range(test_num_left):
            t = threading.Thread(target=do_request, args=(host_url,))
            threads_left.append(t)
            
        for l in range(test_num_left):
            threads_left[l].start()
                
        for l in range(test_num_left):
            threads_left[l].join()
        
    # finish time
    finish_time = time.time()
    time_taken = finish_time - start_time





if __name__ == '__main__':
    print('This is Benchmark, Version 0.1 \n'
          'Copyright 2013 DawnDIY, http://dawndiy.com/ \n'
          'Apache Licence 2.0, http://www.apache.org/licenses/LICENSE-2.0.html')
    print('')
   
    main(sys.argv)
    
    print('Done')
    result()
    
