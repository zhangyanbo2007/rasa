"""
存储pb模型
"""
import tensorflow as tf
def dump_graph_to_pb(pb_path):
    with tf.Session() as sess:
        check_point = tf.train.get_checkpoint_state("./models/nlu/nlu-20200610-234913/nlu")
        if check_point:
            saver = tf.train.import_meta_graph(check_point.model_checkpoint_path + '.meta')
            saver.restore(sess, check_point.model_checkpoint_path)
        else:
            raise ValueError("Model load failed from {}".format(check_point.model_checkpoint_path))

        graph_def = tf.graph_util.convert_variables_to_constants(sess, sess.graph.as_graph_def(), "cal_node".split(","))

        with tf.gfile.GFile(pb_path, "wb") as f:
            f.write(graph_def.SerializeToString())