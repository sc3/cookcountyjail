import eventlet
from random import random

class Parallelizer:
    """
    This runs functions in parallel

    It is used like this:

    import parallelizer  # This iport needs to be before all other imports so eventlet is loaded first

    def my_task(my_args, parallelizer):   # where my_args is an array with arguments about work I have to do
        parallelizer.sleep(1.4)           #       parallelizer is object of Type Parallelizer and provides
        print "Here I am working"         #           some OS capabilities that run off of eventlet, like sleep

    my_servant = Parallelizer(my_task, 25)  # I want 25 my_task's running in parallel
    for i in range(1000):
        my_servant.do_task([i, other_parameters])  # do task requests the work to be done

    # go off and do other work will the tasks work in parallel
    # note that until you do some I/O no tasks will run.

    my_servant.wait_until_tasks_done()              # This will block until all of the workers have completed
                                                    # When this is called, do_task ability is disabled

    # it is ready to be used again
    for i in range(2000):
        my_servant.do_task([i, other_parameters])  # do task requests the work to be done
    my_servant.wait_until_tasks_done()

    """

    __RUN_WORKER_MSG = random()  # generate rand number for this, just for fun
    __KILL_MSG = -1

    def __init__(self, worker_fn, number_of_workers=10):
        self.__worker_fn = worker_fn
        self.__number_of_workers = number_of_workers
        self.__worker_task_queue = eventlet.Queue()
        self.__create_managers()

    def __create_managers(self):
        self.__manager_pool = eventlet.GreenPool()
        for i in range(self.__number_of_workers):
            self.__manager_pool.spawn_n(self.__manager)
        self.__workers_accepting_work = True

    def do_task(self, worker_args):
        if self.__workers_accepting_work:
            self.__worker_task_queue.put((self.__RUN_WORKER_MSG, worker_args))
        else:
            # TODO: decide how to handle this case
            pass

    def __drain_queue(self):
        while not self.__worker_task_queue.empty():
            self.__worker_task_queue.get(block=False)

    def __manager(self):
        run = True
        while run:
            msg_type, worker_args = self.__worker_task_queue.get(block=True)
            if msg_type == self.__RUN_WORKER_MSG:
                self.__worker_fn(worker_args, self)
            else:
                self.__send_kill_msg()  # relay kill msg so other workers will stop
                run = False

    def __send_kill_msg(self):
        self.__worker_task_queue.put((self.__KILL_MSG, []))

    def sleep(self, how_much=1):
        eventlet.sleep(how_much)

    def wait_until_tasks_done(self):
        self.__workers_accepting_work = False   # stop accepting work to do
        self.__send_kill_msg()
        self.__manager_pool.waitall()
        self.__drain_queue()
        self.__create_managers()   # restart workers so they are ready to be used again
