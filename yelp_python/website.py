import sys, os
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
from bottle import route, run, static_file, request
import settings
import app

def renderTable(tuples):
    printResult = """<style type='text/css'> h1 {color:red;} h2 {color:blue;} p {color:green;} </style>
    <table border = '1' frame = 'above'>"""

    header='<tr><th>'+'</th><th>'.join([str(x) for x in tuples[0]])+'</th></tr>'
    data='<tr>'+'</tr><tr>'.join(['<td>'+'</td><td>'.join([str(y) for y in row])+'</td>' for row in tuples[1:]])+'</tr>'
        
    printResult += header+data+"</table>"
    return printResult

@route('/classify_review')
def classify_review():
    r1 = request.query.review_id or "Unknown review id"
    table = app.classify_review(r1)
    return "<html><body>" + renderTable(table) + "</body></html>"
	

@route('/updatezipcode')
def updatezipcode():
    bid = request.query.bid
    zcode = request.query.zcode
    table = app.updatezipcode(bid,zcode)
    return "<html><body>" + renderTable(table) + "</body></html>"
	
@route('/selectTopNbusinesses')
def selectTopNbusinessesWEB():
    class1 = request.query.class1
    n = request.query.n
    table = app.selectTopNbusinesses(class1,n)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/traceUserInfuence')
def traceUserInfuence():
    uid = request.query.userId
    depth = request.query.depth
    table = app.traceUserInfuence(uid,depth)
    return "<html><body>" + renderTable(table) + "</body></html>"

 
@route('/:path')
def callback(path):
    return static_file(path, 'web')

@route('/')
def callback():
    return static_file("index.html", 'web')

run(host='localhost', port=settings.web_port, reloader=True, debug=True)
