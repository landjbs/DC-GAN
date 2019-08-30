"""
Implements base model class for deep convolutional adversarial network
"""

# def assert_types(obj, name, expectedType):
#     """ Helper to assert proper typing of function inputs """
#     assert isinstance(obj, expectedType), f'{name} expected type {expectedType}, but found type {type{obj}}'

import numpy as np
from keras.models import Model, Sequential
from keras.optimizers import RMSprop
from keras.layers import (Input, Conv2D, Activation, LeakyReLU, Dropout,
                            Flatten, Dense, BatchNormalization, ReLU,
                            UpSampling2D, Conv2DTranspose, Reshape)


class GAN(object):

    def __init__(self, name, rowNum, columnNum, channelNum):
        self.name   =   name
        # data formats
        self.rowNum     =   rowNum
        self.columnNum  =   columnNum
        self.channelNum =   channelNum
        self.imageShape =   (rowNum, columnNum, channelNum)
        # model structures
        self.discriminatorStructure =   None
        self.generatorStructure     =   None
        # compiled models
        self.discriminatorCompiled  =   None
        self.adversarialCompiled    =   None
        ## model building params ##
        # default first-layer filter depth of discriminator
        DIS_DEPTH               =   64
        self.DIS_DEPTH          =   DIS_DEPTH
        self.GEN_DEPTH          =   DIS_DEPTH * 4
        # default dropout; should prevent memorization
        self.DROPOUT            =   0.4
        # default kernel size
        self.KERNEL_SIZE        =   5
        # default convolution stride length
        self.STRIDE             =   2
        # default alpha of LeakyReLU activation in discriminator
        self.LEAKY_ALPHA        =   0.2
        # dimensions of generator latent space
        self.LATENT_DIMS        =   100
        # default momentum for adjusting mean and var in generator batch norm
        self.NORM_MOMENTUM      =   0.9

    def __str__():
        built = (self.discriminatorStructure and self.generatorStructure)
        compiled = (self.discriminatorCompiled and self.adversarialCompiled)
        return (f'< GAN_OBJ={self.name} IMAGE_SHAPE={self.imageShape} | ' \
                f'BUILT={built} COMPILED={compiled} >')

    def dis_get_filter_num(self, LAYER_COUNTER):
        """
        Determines number of filters to use on convolution layer assuming layer
        count starts at 1.
        """
        return (self.DIS_DEPTH * (2 ** (LAYER_COUNTER - 1)))

    def gen_get_filter_num(self, LAYER_COUNTER):
        """
        Determines number of filters to use on transpose convolution layer
        assuming filters were generated by dis_get_filter_num() and layer count
        starts at 1.
        """
        return int(self.GEN_DEPTH / (2 ** LAYER_COUNTER))

    class ModelWarning(Warning):
        # BUG: warning currently raises exception instead of warning
        """ Class for warnings related to model building and compiling """
        pass

    def build_discriminator(self):
        """
        Builds discriminator architecture without compiling model.
        Uses functional API to allow for easy insertion of non-sequential
        elements. If the model has already been build, it is simply returned.
        Input has the shape of a single image as specified during object
        initialization. Convolutional layers have a filter number determined
        by self.dis_get_filter_num(LAYER_COUNTER), use self.STRIDES strides
        for downsampling, and pad to match input shape. LeakyReLU functions
        with self.LEAKY_ALPHA alpha are used to give gradients to inactive
        units and self.DROPOUT dropout is used to prevent overfitting.
        Final output is the probability that the image is real, according to
        a single-node, dense layer with sigmoid activation.
        """
        if self.discriminatorStructure:
            raise self.ModelWarning('Discriminator has already been built.')
            return self.discriminatorStructure
        # set up local vars for building
        INPUT_SHAPE     =   self.imageShape
        KERNEL_SIZE     =   self.KERNEL_SIZE
        STRIDE          =   self.STRIDE
        DROPOUT         =   self.DROPOUT
        LEAKY_ALPHA     =   self.LEAKY_ALPHA
        LAYER_COUNTER   =   1
        ## discriminator architecture ##
        inputs = Input(shape=INPUT_SHAPE, name='inputs')
        # first conv block
        conv_1 = Conv2D(filters=self.dis_get_filter_num(LAYER_COUNTER),
                        kernel_size=KERNEL_SIZE,
                        strides=STRIDE,
                        input_shape=INPUT_SHAPE,
                        padding='same',
                        name=f'conv_{LAYER_COUNTER}')(inputs)
        relu_1 = LeakyReLU(LEAKY_ALPHA, name=f'relu_{LAYER_COUNTER}')(conv_1)
        drop_1 = Dropout(rate=DROPOUT, name=f'drop_{LAYER_COUNTER}')(relu_1)
        # second conv block
        LAYER_COUNTER += 1
        conv_2 = Conv2D(filters=self.dis_get_filter_num(LAYER_COUNTER),
                        kernel_size=KERNEL_SIZE,
                        strides=STRIDE,
                        input_shape=INPUT_SHAPE,
                        padding='same',
                        name=f'conv_{LAYER_COUNTER}')(drop_1)
        relu_2 = LeakyReLU(LEAKY_ALPHA, name=f'relu_{LAYER_COUNTER}')(conv_2)
        drop_2 = Dropout(rate=DROPOUT, name=f'drop_{LAYER_COUNTER}')(relu_2)
        # third conv block
        LAYER_COUNTER += 1
        conv_3 = Conv2D(filters=self.dis_get_filter_num(LAYER_COUNTER),
                        kernel_size=KERNEL_SIZE,
                        strides=STRIDE,
                        input_shape=INPUT_SHAPE,
                        padding='same',
                        name=f'conv_{LAYER_COUNTER}')(drop_2)
        relu_3 = LeakyReLU(LEAKY_ALPHA, name=f'relu_{LAYER_COUNTER}')(conv_3)
        drop_3 = Dropout(rate=DROPOUT, name=f'drop_{LAYER_COUNTER}')(relu_3)
        # fourth conv block
        LAYER_COUNTER += 1
        conv_4 = Conv2D(filters=self.dis_get_filter_num(LAYER_COUNTER),
                        kernel_size=KERNEL_SIZE,
                        strides=STRIDE,
                        input_shape=INPUT_SHAPE,
                        padding='same',
                        name=f'conv_{LAYER_COUNTER}')(drop_3)
        relu_4 = LeakyReLU(LEAKY_ALPHA, name=f'relu_{LAYER_COUNTER}')(conv_4)
        drop_4 = Dropout(rate=DROPOUT, name=f'drop_{LAYER_COUNTER}')(relu_4)
        # convolutional output is flattened and passed to dense classifier
        flat = Flatten(name='flat')(drop_4)
        outputs = Dense(units=1, activation='sigmoid', name='outputs')(flat)
        # build sequential model
        discriminatorStructure = Model(inputs=inputs, outputs=outputs)
        print(discriminatorStructure.summary())
        self.discriminatorStructure = discriminatorStructure
        return discriminatorStructure

    def build_generator(self):
        """ Builds generator architecture without compiling model """
        if self.generatorStructure:
            raise self.ModelWarning('Generator has already been built.')
            return self.generatorStructure
        # set up local vars for building
        LATENT_DIMS     =   self.LATENT_DIMS
        KERNEL_SIZE     =   self.KERNEL_SIZE
        DROPOUT         =   self.DROPOUT
        NORM_MOMENTUM   =   self.NORM_MOMENTUM
        GEN_DEPTH       =   self.GEN_DEPTH
        # # TEMP: Find out if other params would be better
        GEN_DIM         =   7
        LATENT_RESHAPE  =   (GEN_DIM, GEN_DIM, GEN_DEPTH)
        LATENT_NODES    =   GEN_DIM * GEN_DIM * GEN_DEPTH
        LAYER_COUNTER   =   1
        ## generator architecture ##
        latent_inputs = Input(shape=(LATENT_DIMS,), name='latent_inputs')
        # dense layer to adjust and norm latent space
        dense_latent = Dense(units=LATENT_NODES,
                            input_dim=LATENT_DIMS,
                            name='dense_latent')(latent_inputs)
        batch_latent = BatchNormalization(momentum=NORM_MOMENTUM,
                                        name='batch_latent')(dense_latent)
        relu_latent = ReLU(name='relu_latent')(batch_latent)
        # reshape latent dims into image shape matrix
        reshaped_latent = Reshape(target_shape=LATENT_RESHAPE,
                                name='reshaped_latent')(relu_latent)
        dropout_latent = Dropout(rate=DROPOUT,
                                name='dropout_latent')(reshaped_latent)
        # first upsampling block
        upsample_1 = UpSampling2D(name=f'upsample_{LAYER_COUNTER}')(dropout_latent)
        transpose_1 = Conv2DTranspose(filters=self.gen_get_filter_num(LAYER_COUNTER),
                                    kernel_size=KERNEL_SIZE,
                                    padding='same',
                                    name=f'transpose_{LAYER_COUNTER}')(upsample_1)
        batch_1 = BatchNormalization(momentum=NORM_MOMENTUM,
                                    name=f'batch_{LAYER_COUNTER}')(transpose_1)
        relu_1 = ReLU(name=f'relu_{LAYER_COUNTER}')(batch_1)
        # second upsampling block
        LAYER_COUNTER += 1
        upsample_2 = UpSampling2D(name=f'upsample_{LAYER_COUNTER}')(relu_1)
        transpose_2 = Conv2DTranspose(filters=self.gen_get_filter_num(LAYER_COUNTER),
                                    kernel_size=KERNEL_SIZE,
                                    padding='same',
                                    name=f'transpose_{LAYER_COUNTER}')(upsample_2)
        batch_2 = BatchNormalization(momentum=NORM_MOMENTUM,
                                    name=f'batch_{LAYER_COUNTER}')(transpose_2)
        relu_2 = ReLU(name=f'relu_{LAYER_COUNTER}')(batch_2)
        # third upsampling block: no upsampling for now
        # QUESTION: Will transpose on final layers lead to artifacts in sharp images?
        LAYER_COUNTER += 1
        transpose_3 = Conv2DTranspose(filters=self.gen_get_filter_num(LAYER_COUNTER),
                                    kernel_size=KERNEL_SIZE,
                                    padding='same',
                                    name=f'transpose_{LAYER_COUNTER}')(relu_2)
        batch_3 = BatchNormalization(momentum=NORM_MOMENTUM,
                                    name=f'batch_{LAYER_COUNTER}')(transpose_3)
        relu_3 = ReLU(name=f'relu_{LAYER_COUNTER}')(batch_3)
        # sigmoid activation on final output to assert grayscale output
        # in range [0, 1]
        output_transpose = Conv2DTranspose(filters=1,
                                            kernel_size=5,
                                            padding='same',
                                            name='output_transpose')(relu_3)
        outputs = Activation(activation='sigmoid')(output_transpose)
        # build sequential model
        generatorStructure = Model(inputs=latent_inputs, outputs=outputs)
        print(generatorStructure.summary())
        self.generatorStructure = generatorStructure
        return generatorStructure

    def compile_discriminator(self):
        """ Compiles discriminator model """
        if self.discriminatorCompiled:
            raise self.ModelWarning('Discriminator has already been compiled.')
            return discriminatorCompiled
        rmsOptimizer = RMSprop(lr=0.0002, decay=6e-8)
        binaryLoss = 'binary_crossentropy'
        discriminatorModel = self.discriminatorStructure
        discriminatorModel.compile(optimizer=rmsOptimizer, loss=binaryLoss,
                                metrics=['accuracy'])
        self.discriminatorCompiled = discriminatorModel
        return discriminatorModel

    def compile_adversarial(self):
        """ Compiles generator model """
        if self.adversarialCompiled:
            raise self.ModelWarning('Adversarial has already been compiled.')
        rmsOptimizer = RMSprop(lr=0.0001, decay=3e-8)
        binaryLoss = 'binary_crossentropy'
        # adversarial built by passing generator output through discriminator
        adversarialModel = Sequential()
        adversarialModel.add(self.generatorStructure)
        adversarialModel.add(self.discriminatorStructure)
        adversarialModel.compile(optimizer=rmsOptimizer, loss=binaryLoss,
                                metrics=['accuracy'])
        self.adversarialCompiled = adversarialModel
        return adversarialModel

    def train_models(self, xTrain, yTrain, xVal=None, yVal=None, xTest=None,
                    yTest=None, steps=2000, batchSize=200):
        """
        Trains discriminator, generator, and adversarial model on x- and yTrain,
        validation on x- and yVal and evaluating final metrics on x- and yTest.
        Generator latent space is initialized with random uniform noise in range
        [-1., 1.].
        Args:
            xTrain:             Training features for discriminator to classify
                                    and generator to 'replicate'.
            yTrain:             Labels for training data.
            xVal (Optional):    Validation features to analyze training
                                    progress. Defaults to None.
            yVal (Optional):    Validation labels to analyze training progress
            xTest (Optional):   Test features to analyze model performance
                                    after training. Defaults to None.
            yTest (Optional):   Test labels to analyze model performance after
                                    training. Defaults to None.
            steps (Optional):   Number of steps to take over the data during
                                    model training. Defaults to 2000.
            batchSize:          Number of examples over which to compute
                                    gradient during model training. Defaults
                                    to 200.
        """

        def shape_assertion(dataset, name):
            """ Asserts that dataset has the proper shape """
            assert (dataset.shape[1:]==self.imageShape), (f'{name} expected ' \
                f'shape {self.imageShape}, but found shape {dataset.shape}.')

        def length_assertion(dataset_1, dataset_2, name_1, name_2):
            """ Asserts that two datasets have the same example number """
            shape_1 = dataset_1.shape[0]
            shape_2 = dataset_2.shape[0]
            assert (shape_1==shape_2), (f'{name_1} and {name_2} should have ' \
            f'the same number of examples, but have {shape_1} and {shape_2}')

        datasetInputs = [('xTrain', xTrain), ('yTrain', yTrain), ('xVal', xVal),
                        ('yVal', yVal), ('xTest', xTest), ('yTest', yTest)]

        for i in range(0, len(datasetInputs), 2):
            # BUG: will break if some datasets are left as none
            name_1, dataset_1 = datasetInputs[i]
            name_2, dataset_2 = datasetInputs[i+1]
            shape_assertion(dataset_1, name_1)
            length_assertion(dataset_1, dataset_2, name_1, name_2)

        assert isinstance(steps, int), ('steps expected type int, but found' \
                                                f'type {type(steps)}.')
        assert (steps > 0), 'steps must be positive'
        assert isinstance(batchSize, int), (f'batchSize expected type int, ' \
                                        'but found type {type(batchSize)}')
        assert (batchSize > 0), 'batchSize must be positive'
        assert (self.discriminatorStructure), ("Desriminator structure has " \
                    "not been built. Try running 'self.build_discriminator()'.")
        assert (self.generatorStructure), ("Generator structure has not been " \
                                "built. Try running 'self.build_generator()'.")
        assert (self.discriminatorCompiled), ("Discriminator model has not " \
                "been compiled. Try running 'self.compile_discriminator()'.")
        assert (self.adversarialCompiled), ("Adversarial model has not been " \
                        "compiled. Try running 'self.compile_adversarial()'.")

        # get number of examples in each dataset
        trainExampleNum = xTrain.shape[0]
        valExampleNum = xVal.shape[0] if (all(xVal) != None) else 0
        testExampleNum = xTest.shape[0] if (all(xTest) != None) else 0

        def batch_discriminator_data(xTrain=xTrain, batchSize=batchSize):
            """
            Builds batch of data for training discriminator comprised of even
            split down batchSize. Half of output data will be a valid example
            of instance from dataset, the other half will be invalid examples
            initialized as a random-uniform noise vector of latentDims to be
            passed to generator and discriminated after upsampling.
            Args:
                xTrain:         Dataset of features for training
                batchSize:      Batch size for training
            Returns:
                4th order tensor of valid and invalid features of shape
                ((2 * batchSize), rowNum, columnNum, channelNum) and vector of
                target labels of length batchSize for discriminator training
                (0 - invalid, 1 - valid) in tuple of form (features, targets).
            """
            # select random batchSize examples from xTrain
            selectionIndex = np.random.randint(low=0, high=trainExampleNum,
                                                size=batchSize)
            validExamples = xTrain[selectionIndex, :, :, :]
            validTargets = np.ones(shape=(batchSize,))
            # initialize noise vector for latent space
            noiseLatent = np.random.uniform(low=-1.0, high=1.0,
                                            size=(batchSize, self.LATENT_DIMS))
            # pass noise vector through generator to get noise images
            invalidExamples = self.generatorStructure.predict(noiseLatent)
            invalidTargets = np.zeros(shape=(batchSize,))
            # concatenate features and targets and return
            features = np.concatenate([validExamples, invalidExamples])
            targets = np.concatenate([validTargets, invalidTargets])
            return features, targets

        def batch_adversarial_data(batchSize=batchSize):
            """
            Generates batch of training data for adversarial network. Here,
            every example is a random vector of length latentDims and every
            label is valid (1). The goal of the generator within the adversarial
            model is to create an output from the noise vector who's 'validity
            score' has minimum binary crossentropy loss with respect to 1.0
            as output by the discriminator within the adversarial model.
            Args:
                batchSize:      Batch size for training
            Returns:
                2nd order tensor of shape (batchSize, latentDims) containing
                noise vectors for initializing the generator and vector of
                target labels (all 1's - valid) in tuple of form (features,
                targets).
            """
            noiseLatent = np.random.uniform(low=-1.0, high=1.0,
                                            size=(batchSize, self.LATENT_DIMS))
            targets = np.ones(shape=(batchSize,))
            return (noiseLatent, targets)

        for curStep in range(steps):
            # train discriminator on valid and invalid images
            disFeatures, disTargets = batch_discriminator_data()
            disData = self.discriminatorCompiled.train_on_batch(x=disFeatures,
                                                                y=disTargets)
            # train adversarial network
            advFeatures, advTargets = batch_adversarial_data()
            advData = self.adversarialCompiled.train_on_batch(x=advFeatures,
                                                            y=advTargets)
            # format and log
            disLoss, disAcc = round(disData[0], 4), round(disData[1], 4)
            advLoss, advAcc = round(advData[0], 4), round(advData[1], 4)
            print(f'Step: {curStep}\n\t' \
                f'D [loss: {disLoss} acc: {disAcc}]\n\t' \
                f'A [loss: {advLoss} acc: {advAcc}]')

            if ((curStep % 100) == 0):
                self.adversarialCompiled.save('adversarialModel.h5')
