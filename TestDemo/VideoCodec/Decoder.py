import pickle
import tensorflow as tf
from imageio import imread,imwrite
import numpy as np
from argparse import ArgumentParser
import math

def CalcuPSNR(target, ref):
    diff = ref - target
    diff = diff.flatten('C')
    rmse = math.sqrt(np.mean(diff**2.))
    return 20 * math.log10(1.0 / (rmse))


def load_graph(frozen_graph_filename):
    with tf.io.gfile.GFile(frozen_graph_filename, "rb") as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())

    with tf.compat.v1.Graph().as_default() as graph:
        tf.import_graph_def(graph_def)

    if True:
        with open('dec_net.txt', 'a') as file:
            for node in graph_def.node:
                # print(f"Node name: {node.name}, Op type: {node.op}")
                print(f"Node name: {node.name}, Op type: {node.op}", file=file)

    writer = tf.summary.create_file_writer('./declogs')
    with writer.as_default():
        tf.summary.graph(graph)

    return graph

def array_to_png(image_array, output_path, shape):
    image_array = np.reshape(image_array, shape)
    image_array = np.clip(image_array * 255, 0, 255).astype(np.uint8)
    imwrite(output_path, image_array)

def decoder(loadmodel, refer_path, outputfolder):
    graph = load_graph(loadmodel)

    reconframe = graph.get_tensor_by_name('import/build_towers/tower_0/train_net_inference_one_pass/train_net/ReconFrame:0')
    res_input = graph.get_tensor_by_name('import/quant_feature:0')
    res_prior_input = graph.get_tensor_by_name('import/quant_z:0')
    motion_input = graph.get_tensor_by_name('import/quant_mv:0')
    previousImage = graph.get_tensor_by_name('import/input_image_ref:0')

    with tf.compat.v1.Session(graph=graph) as sess:

        with open(outputfolder + 'quantized_res_feature.pkl', 'rb') as f:
            residual_feature = pickle.load(f)

        with open(outputfolder + 'quantized_res_prior_feature.pkl', 'rb') as f:
            residual_prior_feature = pickle.load(f)

        with open(outputfolder + 'quantized_motion_feature.pkl', 'rb') as f:
            motion_feature = pickle.load(f)

        im_ori = imread(refer_path)
        im1 = imread(refer_path)
        im1 = im1 / 255.0
        im1 = np.expand_dims(im1, axis=0)

        # reconstructed image
        recon_d = sess.run(
            [reconframe],
            feed_dict={
                res_input: residual_feature,
                res_prior_input: residual_prior_feature,
                motion_input: motion_feature,
                previousImage: im1
            })

        # print(recon_d)
        array_to_png(recon_d, "./image/recon.png", im_ori.shape)
        # check 
        # imagedir = './image/'
        # im2 = imread(imagedir + 'im003.png')
        # im2 = im2 / 255.0
        # im2 = np.expand_dims(im2, axis=0)
        # print(CalcuPSNR(im2, recon_d))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--DecoderModel', type=str, dest="loadmodel", default='./model/L2048/frozen_model_D.pb', help="decoder model")
    parser.add_argument('--refer_frame', type=str, dest="refer_path", default='./image/im001.png', help="refer image path")
    parser.add_argument('--loadpath', type=str, dest="outputfolder", default='./testpkl/', help="saved pkl file")

    args = parser.parse_args()
    decoder(**vars(args))