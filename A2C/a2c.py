import numpy as np

from keras.models import Model
from keras import regularizers
from keras.layers import Input, Dense, Conv2D, MaxPooling2D, Dropout, BatchNormalization, Flatten

from critic import Critic
from actor import Actor

class A2C:
    """ Actor-Critic Main Algorithm
    """

    def __init__(self, act_dim, env_dim, gamma = 0.99, lr = 0.001):
        """ Initialization
        """
        # Create actor and critic networks
        self.act_dim = act_dim
        self.env_dim = env_dim
        self.gamma = gamma
        self.shared = self.buildNetwork()
        self.actor = Actor(env_dim, act_dim, self.shared, lr)
        self.critic = Critic(env_dim, act_dim, self.shared, 5 * lr)

    def buildNetwork(self):
        """ Assemble shared layers
        """
        inp = Input((self.env_dim))
        # If we have an image, apply convolutional layers
        if(len(self.env_dim) > 2):
            x = self.conv_block(inp, 32)
            x = self.conv_block(x, 32)
            x = Flatten()(x)
            x = Dense(32, activation='relu', kernel_initializer='he_uniform')(x)
        else:
            x = Dense(128, activation='relu', kernel_initializer='he_uniform')(inp)
        return Model(inp, x)

    def conv_layer(self, d):
        """ Returns a 2D Conv layer, with L2-regularization and ReLU activation
        """
        return Conv2D(d, 3,
            activation = 'relu',
            padding = 'same',
            kernel_initializer = 'he_normal',
            kernel_regularizer = regularizers.l2(0.001))

    def conv_block(self, inp, d):
        """ Returns a 2D Conv block, with a convolutional layer, max-pooling,
        dropout and batch-normalization --- // TODO TRY INCEPTION ? //
        """
        conv = self.conv_layer(d)(inp)
        pool = MaxPooling2D(pool_size=(2, 2))(conv)
        bn = BatchNormalization()(pool)
        drop = Dropout(0.3)(bn)
        return pool

    def policy_action(self, s):
        """ Use the actor to predict the next action to take, using the policy
        """
        return np.random.choice(np.arange(self.act_dim), 1, p=self.actor.predict(s).ravel())[0]

    def train(self, s_0, a, r, s_1, done):
        """ Update actor and critic networks from experience
        """
        # Estimate state values using critic
        V_0 = self.critic.predict(s_0)
        V_1 = self.critic.predict(s_1)

        # Compute actor and critic training targets
        critic_t, actor_t = 0, np.zeros((1, self.act_dim))
        if done:
            critic_t = r
            actor_t[0][a] = r - V_0
        else:
            critic_t = r + self.gamma * V_1  # State Value Update
            actor_t[0][a] = r + self.gamma * V_1 - V_0 # Advantage

        # Train Actor and Critic
        self.actor.fit(s_0, actor_t)
        self.critic.fit(s_0, np.full((1, 1), critic_t))
