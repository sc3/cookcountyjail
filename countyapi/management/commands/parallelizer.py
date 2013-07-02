import eventlet


class Parallelizer:
    """
    This runs functions in parallel using the Eventlet library to accomplish
    the parallelization. This is basically what Twisted does.
    If you have computation heavy with no I/O or almost none, then this will
    not provide any advantage.

    Eventlet re-writes standard libraries so either it or this must be loaded
    first in your program.

    It is used like this sample program:

    from parallelizer import Parallelizer  # First library loaded
    import xxx

    # Now your function that is to be run in parallel
    # my_args is an array with arguments to be used when doing the work
    # parallelizer is the instance of Parallelizer that is running this
    #      function in parallel, provides Eventlet OS re-written sevices
    #      like sleep
    def my_task(my_args, parallelizer):
        parallelizer.sleep(1.4)
        print "Hey I doing my work, here"

    my_servant = Parallelizer(my_task, 25)  # 25 my_task's running in parallel
    for i in range(1000):
        my_servant.do_task([i, other_parameters])  # send work for tasks to
                                                   # process, queue as many
                                                   # of these as you want

    # Now go off and do other work and if you use I/O then the queued tasks
    # will be worked on in parallel, if you do no I/O then no taks will run
    # until you do the following:

    my_servant.wait_until_tasks_done()  # This will block until all of the
                                        # workers have completed. Note, that
                                        # when this is called, do_task ability
                                        # is disabled

    # When all the tasks have completed control is returned to this point and
    # the parallelizer instance is is ready to be used again
    for i in range(2000):
        my_servant.do_task([i, other_parameters])
    my_servant.wait_until_tasks_done()

    """

    __KILL_MSG = -2013
    __RUN_WORKER_MSG = ~__KILL_MSG
    __manager_pool = None
    __workers_accepting_work = False

    def __init__(self, worker_fn, number_of_workers=10):
        self.__worker_fn = worker_fn
        self.__number_of_workers = number_of_workers
        self.__worker_task_queue = eventlet.Queue()  # infinite size queue
        self.__create_managers()

    # creates a manager for each worker
    def __create_managers(self):
        if self.__manager_pool is not None:
            self.__manager_pool = eventlet.GreenPool()
            for i in range(self.__number_of_workers):
                self.__manager_pool.spawn_n(self.__manager)
            self.__workers_accepting_work = True

    # Only accepts work if method wait_until_tasks_done is not being executed
    def do_task(self, worker_args):
        if self.__workers_accepting_work:
            self.__worker_task_queue.put((self.__RUN_WORKER_MSG, worker_args))
        else:
            # TODO: decide how to handle this case
            pass

    def __drain_queue(self):
        while not self.__worker_task_queue.empty():
            self.__worker_task_queue.get(block=False)

    # manager fetches messages from queue and calls worker function with passed
    # arguments. When worker function finishes tries to get data from queue.
    # If nothing to get blocks. Checks for Kill Message if it receives it
    # stops running.
    def __manager(self):
        run = True
        while run:
            msg_type, worker_args = self.__worker_task_queue.get(block=True)
            if msg_type == self.__KILL_MSG:
                self.__send_kill_msg()  # relay kill msg so other workers
                run = False             # will be stopped as well
            else:
                self.__worker_fn(worker_args, self)

    def __send_kill_msg(self):
        self.__worker_task_queue.put((self.__KILL_MSG, []))

    # provides an Eventlet based sleep so other workers will run while this
    # one sleeps. Like all sleeps, this one does not guarantee exactness of
    # the length of the sleep
    def sleep(self, how_much=0.1):
        eventlet.sleep(how_much)

    # use this to complete worker processing. Once all workers have completed
    # their processing then this will respawn the managers and return
    def wait_until_tasks_done(self):
        self.__workers_accepting_work = False   # stop accepting work to do
        self.__send_kill_msg()
        self.__manager_pool.waitall()
        self.__drain_queue()  # remove residual kill messages
        self.__create_managers()   # restart managers so workers are ready to
                                   # be used again
