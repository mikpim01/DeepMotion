# import third-party packages
import tensorflow as tf
from tensorflow.contrib import rnn
from sklearn.model_selection import train_test_split

import numpy as np
import logging
import csv
import datetime
import time


# constant for logger
CURRENT_TIMESTAMP = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S')
RESULT_OUTPUT = 'run_svm_result_' + CURRENT_TIMESTAMP + '.log'
LOGGER_FORMAT_HEADER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
CUTOFF_LINE = '--------------------------------------------------------------------------------------------------'


# general constant
SPLIT_RANDOM_STATE = 42
TEST_SIZE = 0.25


# constant for rnn training
learning_rate = 0.001
training_steps = 1000
batch_size = 128
display_step = 50

# constant rnn network parameters
num_input = 3  # we only read one set of yaw pitch row
timesteps = 100  # timesteps - we have 100 data point for each char
num_hidden = 128  # hidden layer num of features
num_classes = 3  # number of data class - using abc for now

# raw data file names
DATA_SET_A = 'run_letter_a_format.csv'
DATA_SET_B = 'run_letter_b_format.csv'
DATA_SET_C = 'run_letter_c_format.csv'
DATA_SET_D = 'run_letter_d_format.csv'
DATA_SET_E = 'run_letter_e_format.csv'

# tf Graph input
X = tf.placeholder("float", [None, timesteps, num_input])
Y = tf.placeholder("float", [None, num_classes])

# Define weights
weights = {
    'out': tf.Variable(tf.random_normal([num_hidden, num_classes]))
}
biases = {
    'out': tf.Variable(tf.random_normal([num_classes]))
}


def read_format_input(read_file_name):
    with open(read_file_name, 'r') as f:
        reader = csv.reader(f)
        raw_data_list = list(reader)

    return raw_data_list


def render_raw_data():
    raw_a_x = np.array(read_format_input(DATA_SET_A)).astype(None)
    raw_b_x = np.array(read_format_input(DATA_SET_B)).astype(None)
    raw_c_x = np.array(read_format_input(DATA_SET_C)).astype(None)
    raw_d_x = np.array(read_format_input(DATA_SET_D)).astype(None)
    raw_e_x = np.array(read_format_input(DATA_SET_E)).astype(None)
    raw_x = np.concatenate((raw_a_x, raw_b_x, raw_c_x, raw_d_x, raw_e_x), axis=0)

    raw_a_y = np.array([[1, 0, 0, 0, 0]] * len(raw_a_x)).astype(None)
    raw_b_y = np.array([[0, 1, 0, 0, 0]] * len(raw_b_x)).astype(None)
    raw_c_y = np.array([[0, 0, 1, 0, 0]] * len(raw_c_x)).astype(None)
    raw_d_y = np.array([[0, 0, 0, 1, 0]] * len(raw_d_x)).astype(None)
    raw_e_y = np.array([[0, 0, 0, 0, 1]] * len(raw_e_x)).astype(None)
    raw_y = np.concatenate((raw_a_y, raw_b_y, raw_c_y, raw_d_y, raw_e_y), axis=0)

    train_x, test_x, train_y, test_y = \
        train_test_split(raw_x, raw_y, test_size=TEST_SIZE, random_state=SPLIT_RANDOM_STATE)

    return train_x, train_y, test_x, test_y


def RNN(x, weights, biases):
    # Prepare data shape to match `rnn` function requirements
    # Current data input shape: (batch_size, timesteps, n_input)
    # Required shape: 'timesteps' tensors list of shape (batch_size, n_input)

    # Unstack to get a list of 'timesteps' tensors of shape (batch_size, n_input)
    x = tf.unstack(x, timesteps, 1)

    # Define a lstm cell with tensorflow
    lstm_cell = rnn.BasicLSTMCell(num_hidden, forget_bias=1.0)

    # Get lstm cell output
    outputs, states = rnn.static_rnn(lstm_cell, x, dtype=tf.float32)

    # Linear activation, using rnn inner loop last output
    return tf.matmul(outputs[-1], weights['out']) + biases['out']


def training_engine(train_x, train_y, test_x, test_y):
    logits = RNN(X, weights, biases)
    prediction = tf.nn.softmax(logits)

    # Define loss and optimizer
    loss_op = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
        logits=logits, labels=Y))
    optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate)
    train_op = optimizer.minimize(loss_op)

    # Evaluate model (with test logits, for dropout to be disabled)
    correct_pred = tf.equal(tf.argmax(prediction, 1), tf.argmax(Y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

    # Initialize the variables (i.e. assign their default value)
    init = tf.global_variables_initializer()

    # Start training
    with tf.Session() as sess:

        # Run the initializer
        sess.run(init)

        for step in range(1, training_steps + 1):
            batch_x, batch_y = mnist.train.next_batch(batch_size)
            # Reshape data to get 28 seq of 28 elements
            batch_x = batch_x.reshape((batch_size, timesteps, num_input))
            # Run optimization op (backprop)
            sess.run(train_op, feed_dict={X: batch_x, Y: batch_y})
            if step % display_step == 0 or step == 1:
                # Calculate batch loss and accuracy
                loss, acc = sess.run([loss_op, accuracy], feed_dict={X: batch_x,
                                                                     Y: batch_y})
                print("Step " + str(step) + ", Minibatch Loss= " + \
                      "{:.4f}".format(loss) + ", Training Accuracy= " + \
                      "{:.3f}".format(acc))

        print("Optimization Finished!")

        # Calculate accuracy for 128 mnist test images
        test_len = 128
        test_data = mnist.test.images[:test_len].reshape((-1, timesteps, num_input))
        test_label = mnist.test.labels[:test_len]
        print("Testing Accuracy:", \
              sess.run(accuracy, feed_dict={X: test_data, Y: test_label}))


def main():
    logger = logging.getLogger('cogs181_runtime')
    logger.setLevel(logging.DEBUG)
    # fh = logging.FileHandler(RESULT_OUTPUT)
    # fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOGGER_FORMAT_HEADER)
    # fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.debug("Start reading formatted input")
    train_x, train_y, test_x, test_y = render_raw_data()
    logger.debug("End reading formatted input")

    # training_engine(train_x, train_y, test_x, test_y)


if __name__ == '__main__':
    main()
