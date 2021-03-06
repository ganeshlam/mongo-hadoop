#!/bin/env python

import unittest
import pymongo
import mongo_manager
import subprocess
import os
from datetime import timedelta
import time
HADOOP_HOME=os.environ['HADOOP_HOME']
#declare -a job_args
#cd ..

# result set for sanity check#{{{
check_results = [ { "_id": 1990, "count": 250, "avg": 8.552400000000002, "sum": 2138.1000000000004 }, 
                  { "_id": 1991, "count": 250, "avg": 7.8623600000000025, "sum": 1965.5900000000006 },
                  { "_id": 1992, "count": 251, "avg": 7.008844621513946, "sum": 1759.2200000000005 },
                  { "_id": 1993, "count": 250, "avg": 5.866279999999999, "sum": 1466.5699999999997 },
                  { "_id": 1994, "count": 249, "avg": 7.085180722891565, "sum": 1764.2099999999996 },
                  { "_id": 1995, "count": 250, "avg": 6.573920000000002, "sum": 1643.4800000000005 },
                  { "_id": 1996, "count": 252, "avg": 6.443531746031742, "sum": 1623.769999999999 },
                  { "_id": 1997, "count": 250, "avg": 6.353959999999992, "sum": 1588.489999999998 },
                  { "_id": 1998, "count": 250, "avg": 5.262879999999994, "sum": 1315.7199999999984 },
                  { "_id": 1999, "count": 251, "avg": 5.646135458167332, "sum": 1417.1800000000003 },
                  { "_id": 2000, "count": 251, "avg": 6.030278884462145, "sum": 1513.5999999999985 },
                  { "_id": 2001, "count": 248, "avg": 5.02068548387097, "sum": 1245.1300000000006 },
                  { "_id": 2002, "count": 250, "avg": 4.61308, "sum": 1153.27 },
                  { "_id": 2003, "count": 250, "avg": 4.013879999999999, "sum": 1003.4699999999997 },
                  { "_id": 2004, "count": 250, "avg": 4.271320000000004, "sum": 1067.8300000000008 },
                  { "_id": 2005, "count": 250, "avg": 4.288880000000001, "sum": 1072.2200000000003 },
                  { "_id": 2006, "count": 250, "avg": 4.7949999999999955, "sum": 1198.7499999999989 },
                  { "_id": 2007, "count": 251, "avg": 4.634661354581674, "sum": 1163.3000000000002 },
                  { "_id": 2008, "count": 251, "avg": 3.6642629482071714, "sum": 919.73 },
                  { "_id": 2009, "count": 250, "avg": 3.2641200000000037, "sum": 816.0300000000009 },
                  { "_id": 2010, "count": 189, "avg": 3.3255026455026435, "sum": 628.5199999999996 } ]#}}}
                             
                             
def compare_results(collection):
    output = list(collection.find().sort("_id"))
    if len(output) != len(check_results):
        print "count is not same", len(output), len(check_results)
        print output
        return False
    for i, doc in enumerate(output):
        #round to account for slight changes due to precision in case ops are run in different order.
        if doc['_id'] != check_results[i]['_id'] or \
                doc['count'] != check_results[i]['count'] or \
                round(doc['avg'], 7) != round(check_results[i]['avg'], 7): 
            print "docs do not match", doc, check_results[i]
            return False
    return True


MONGO_HADOOP_ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBJAR_PATH=os.path.join(MONGO_HADOOP_ROOT,
    "examples",
    "treasury_yield",
    "target",
    "treasury-example_*.jar")
JSONFILE_PATH=os.path.join(MONGO_HADOOP_ROOT,
    'examples',
    'treasury_yield',
    'src',
    'main',
    'resources',
    'yield_historical_in.json')

STREAMING_JARPATH=os.path.join(MONGO_HADOOP_ROOT,
    "streaming",
    "target",
    "mongo-hadoop-streaming*.jar")
STREAMING_MAPPERPATH=os.path.join(MONGO_HADOOP_ROOT,
    "streaming",
    "examples",
    "treasury",
    "mapper.py")

STREAMING_REDUCERPATH=os.path.join(MONGO_HADOOP_ROOT,
    "streaming",
    "examples",
    "treasury",
    "reducer.py")

DEFAULT_PARAMETERS = {
  "mongo.job.verbose":"true",
  "mongo.job.background":"false",
  #"mongo.input.key":"",
  #"mongo.input.query":"",
  "mongo.job.mapper":"com.mongodb.hadoop.examples.treasury.TreasuryYieldMapper",
  "mongo.job.reducer":"com.mongodb.hadoop.examples.treasury.TreasuryYieldReducer",
  "mongo.job.input.format":"com.mongodb.hadoop.MongoInputFormat",
  "mongo.job.output.format":"com.mongodb.hadoop.MongoOutputFormat",
  "mongo.job.output.key":"org.apache.hadoop.io.IntWritable",
  "mongo.job.output.value":"org.apache.hadoop.io.DoubleWritable",
  "mongo.job.mapper.output.key":"org.apache.hadoop.io.IntWritable",
  "mongo.job.mapper.output.value":"com.mongodb.hadoop.io.BSONWritable",
  #"mongo.job.combiner":"com.mongodb.hadoop.examples.treasury.TreasuryYieldReducer",
  "mongo.job.partitioner":"",
  "mongo.job.sort_comparator":"",
}

def runjob(hostname, params, input_collection='mongo_hadoop.yield_historical.in',
           output_collection='mongo_hadoop.yield_historical.out', output_hostnames=[], readpref="primary"):
    cmd = [os.path.join(HADOOP_HOME, "bin", "hadoop")]
    cmd.append("jar")
    cmd.append(JOBJAR_PATH)

    for key, val in params.items():
        cmd.append("-D")
        cmd.append(key + "=" + val)

    cmd.append("-D")
    cmd.append("mongo.input.uri=mongodb://%s/%s?readPreference=%s" % (hostname, input_collection, readpref))
    cmd.append("-D")
    if not output_hostnames:# just use same as input host name
        cmd.append("mongo.output.uri=mongodb://%s/%s" % (hostname, output_collection))
    else:
        output_uris = ['mongodb://%s/%s' % (host, output_collection) for host in output_hostnames]
        cmd.append("mongo.output.uri=\"" + ' '.join(output_uris) + "\"")

    print cmd
    subprocess.call(' '.join(cmd), shell=True)

def runstreamingjob(hostname, params, input_collection='mongo_hadoop.yield_historical.in',
           output_collection='mongo_hadoop.yield_historical.out', readpref="primary"):
    cmd = [os.path.join(HADOOP_HOME, "bin", "hadoop")]
    cmd.append("jar")
    cmd.append(STREAMING_JARPATH)

    for key, val in params.items():
        cmd.append("-" + key)
        cmd.append(val)

    cmd.append("-inputURI")
    cmd.append("mongodb://%s/%s?readPreference=%s" % (hostname, input_collection, readpref))
    cmd.append("-outputURI")
    cmd.append("mongodb://%s/%s" % (hostname, output_collection))

    print cmd
    subprocess.call(' '.join(cmd), shell=True)


class Standalone(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.server = mongo_manager.StandaloneManager(home="/tmp/standalone1")  
        self.server_hostname = self.server.start_server(fresh=True)
        self.server.connection().drop_database('mongo_hadoop')
        mongo_manager.mongo_import(self.server_hostname,
                                   "mongo_hadoop",
                                   "yield_historical.in",
                                   JSONFILE_PATH)
        print "server is ready."

    def setUp(self):
        self.server.connection()['mongo_hadoop']['yield_historical.out'].drop()


    @classmethod
    def tearDownClass(self):
        print "standalone clas: killing mongod"
        self.server.kill_all_members()

class TestBasic(Standalone):

    def test_treasury(self):
        runjob(self.server_hostname, DEFAULT_PARAMETERS)
        out_col = self.server.connection()['mongo_hadoop']['yield_historical.out']
        self.assertTrue(compare_results(out_col))


class BaseShardedTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.shard1 = mongo_manager.ReplicaSetManager(home="/tmp/rs0",
                with_arbiter=True,
                num_members=3)
        self.shard1.start_set(fresh=True)
        self.shard2 = mongo_manager.ReplicaSetManager(home="/tmp/rs1",
                with_arbiter=True,
                num_members=3)
        self.shard2.start_set(fresh=True)
        self.configdb = mongo_manager.StandaloneManager(home="/tmp/config_db")  
        self.confighost = self.configdb.start_server(fresh=True)

        self.mongos = mongo_manager.MongosManager(home="/tmp/mongos")
        self.mongos_hostname = self.mongos.start_mongos(self.confighost,
                [h.get_shard_string() for h in (self.shard1,self.shard2)],
                noauth=False, fresh=True, addShards=True)

        self.mongos2 = mongo_manager.MongosManager(home="/tmp/mongos2")
        self.mongos2_hostname = self.mongos2.start_mongos(self.confighost,
                [h.get_shard_string() for h in (self.shard1,self.shard2)],
                noauth=False, fresh=True, addShards=False)

        self.mongos_connection = self.mongos.connection()
        self.mongos2_connection = self.mongos2.connection()
        self.mongos_connection.drop_database('mongo_hadoop')
        mongo_manager.mongo_import(self.mongos_hostname,
                                   "mongo_hadoop",
                                   "yield_historical.in",
                                   JSONFILE_PATH)
        mongos_admindb = self.mongos_connection['admin']
        mongos_admindb.command("enablesharding", "mongo_hadoop")

        #turn off the balancer
        self.mongos_connection['config'].settings.update({ "_id": "balancer" }, { '$set' : { 'stopped': True } }, True );
        mongos_admindb.command("shardCollection",
                "mongo_hadoop.yield_historical.in",
                key={"_id":1})

        testcoll = self.mongos_connection['mongo_hadoop']['yield_historical.in']

        for chunkpos in [2000, 3000, 1000, 500, 4000, 750, 250, 100, 3500, 2500, 2250, 1750]:
            mongos_admindb.command("split", "mongo_hadoop.yield_historical.in",
                    middle={"_id":testcoll.find().sort("_id", 1).skip(chunkpos).limit(1)[0]['_id']})

        ms_config = self.mongos_connection['config']
        shards = list(ms_config.shards.find())
        numchunks = ms_config.chunks.count()
        chunk_source = ms_config.chunks.find_one()['shard']
        print "chunk source", chunk_source
        chunk_dest = [s['_id'] for s in shards if s['_id'] != chunk_source][0]
        print "chunk dest", chunk_dest
        #shuffle chunks around
        for i in xrange(0, numchunks/2):
            chunk_to_move = ms_config.chunks.find_one({"shard":chunk_source})
            print "moving", chunk_to_move, "from", chunk_source, "to", chunk_dest
            try:
                mongos_admindb.command("moveChunk", "mongo_hadoop.yield_historical.in", find=chunk_to_move['min'], to=chunk_dest);
            except Exception, e:
                print e

        time.sleep(5)

    def setUp(self):
        self.mongos_connection['mongo_hadoop']['yield_historical.out'].drop()

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(self):
        print "killing sharded servers!"
        self.mongos.kill_all_members()
        self.shard1.kill_all_members()
        self.shard2.kill_all_members()
        self.configdb.kill_all_members()


class TestSharded(BaseShardedTest):
    #run a simple job against a sharded cluster, going against the mongos directly

    def test_treasury(self):
        runjob(self.mongos_hostname, DEFAULT_PARAMETERS)
        out_col = self.mongos_connection['mongo_hadoop']['yield_historical.out']
        self.assertTrue(compare_results(out_col))

    def test_treasury_multi_mongos(self):
        print "before"
        print self.mongos_connection['admin'].command("serverStatus")['opcounters']
        print self.mongos2_connection['admin'].command("serverStatus")['opcounters']
        runjob(self.mongos_hostname, DEFAULT_PARAMETERS, output_hostnames=[self.mongos_hostname, self.mongos2_hostname])
        out_col = self.mongos_connection['mongo_hadoop']['yield_historical.out']
        print "after"
        print self.mongos_connection['admin'].command("serverStatus")['opcounters']
        print self.mongos2_connection['admin'].command("serverStatus")['opcounters']
        self.assertTrue(compare_results(out_col))

class TestShardedGTE_LT(BaseShardedTest):

    def test_gte_lt(self):
        PARAMETERS = DEFAULT_PARAMETERS.copy()
        PARAMETERS['mongo.input.split.use_range_queries'] = 'true'

        shard1db = pymongo.Connection(self.shard1.get_primary()[0])['mongo_hadoop']
        shard2db = pymongo.Connection(self.shard2.get_primary()[0])['mongo_hadoop']
        shard1db.set_profiling_level(2)
        shard2db.set_profiling_level(2)
        runjob(self.mongos_hostname, PARAMETERS)
        out_col = self.mongos_connection['mongo_hadoop']['yield_historical.out']
        self.assertTrue(compare_results(out_col))
        print "showing profiler results"
        for line in list(shard1db['system.profile'].find({"ns":'mongo_hadoop.yield_historical.in', "op":"query"}, {"query":1})):
            print line

        for line in list(shard2db['system.profile'].find({"ns":'mongo_hadoop.yield_historical.in', "op":"query"}, {"query":1})):
            print line

        PARAMETERS['mongo.input.query'] = '{"_id":{"\$gt":{"\$date":1182470400000}}}'
        out_col.drop()
        runjob(self.mongos_hostname, PARAMETERS)
        #Make sure that this fails when rangequery is used with a query that conflicts
        self.assertEqual(out_col.count(), 0)

        for line in list(shard1db['system.profile'].find({"ns":'mongo_hadoop.yield_historical.in', "op":"query"}, {"query":1})):
            print line

class TestShardedNoMongos(BaseShardedTest):
    #run a simple job against a sharded cluster, going directly to shards (bypass mongos)

    def test_treasury(self):
        #PARAMETERS = DEFAULT_PARAMETERS.copy()
        #PARAMETERS['mongo.input.split.read_shard_chunks'] = 'true'
        #print "running job against shards directly"
        #runjob(self.mongos_hostname, PARAMETERS)
        #out_col = self.mongos_connection['mongo_hadoop']['yield_historical.out']
        #self.assertTrue(compare_results(out_col))

        self.mongos_connection['mongo_hadoop']['yield_historical.out'].drop()

        #HADOOP61 - simulate a failed migration by having some docs from one chunk
        #also exist on another shard who does not own that chunk (duplicates)
        ms_config = self.mongos_connection['config']

        print list(ms_config.shards.find())
        print list(ms_config.chunks.find())
        chunk_to_duplicate = ms_config.chunks.find_one({"shard":self.shard1.name})
        print "duplicating chunk", chunk_to_duplicate
        chunk_query = {"_id":{"$gte":chunk_to_duplicate['min']['_id'], "$lt": chunk_to_duplicate['max']['_id']}}
        data_to_duplicate = list(self.mongos_connection['mongo_hadoop']['yield_historical.in'].find(chunk_query))
        destination = pymongo.Connection(self.shard2.get_primary()[0])
        for doc in data_to_duplicate:
            #print doc['_id'], "was on shard ", self.shard1.name, "now on ", self.shard2.name
            #print "inserting", doc
            destination['mongo_hadoop']['yield_historical.in'].insert(doc, safe=True)
        
        PARAMETERS = DEFAULT_PARAMETERS.copy()
        PARAMETERS['mongo.input.split.allow_read_from_secondaries'] = 'true'
        PARAMETERS['mongo.input.split.read_from_shards'] = 'true'
        PARAMETERS['mongo.input.split.read_shard_chunks'] = 'false'
        runjob(self.mongos_hostname, PARAMETERS, readpref="secondary")

        out_col2 = self.mongos_connection['mongo_hadoop']['yield_historical.out']
        self.assertFalse(compare_results(out_col2))
        self.mongos_connection['mongo_hadoop']['yield_historical.out'].drop()

        PARAMETERS = DEFAULT_PARAMETERS.copy()
        PARAMETERS['mongo.input.split.allow_read_from_secondaries'] = 'true'
        PARAMETERS['mongo.input.split.read_from_shards'] = 'true'
        PARAMETERS['mongo.input.split.read_shard_chunks'] = 'true'
        runjob(self.mongos_hostname, PARAMETERS, readpref="secondary")
        self.assertTrue(compare_results(out_col2))

class TestStreaming(Standalone):

    def test_treasury(self):
        runstreamingjob(self.server_hostname, {'mapper': STREAMING_MAPPERPATH, 'reducer':STREAMING_REDUCERPATH})
        out_col = self.server.connection()['mongo_hadoop']['yield_historical.out']
        self.assertTrue(compare_results(out_col))
        #runjob(self.server_hostname, DEFAULT_PARAMETERS)

def testtreasury():
    runjob('localhost:4007')

if __name__ == '__main__': testtreasury()
