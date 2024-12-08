"""The main infretis loop."""

from infretis.setup import setup_internal, setup_runner
import tracemalloc

def scheduler(config):
    tracemalloc.start()  # Start tracing memory allocations

    snapshot_start = tracemalloc.take_snapshot()
    """Run infretis loop."""
    # setup repex, runner and futures
    md_items, state = setup_internal(config)
    runner, futures = setup_runner(state)

    # submit the first number of workers
    while state.initiate():
        # pick and prep ens and path for the next job
        md_items = state.prep_md_items(md_items)

        # submit job to scheduler
        futures.add(runner.submit_work(md_items))

    # main step loop
    while state.loop():
        # Get futures as they are completed
        future = futures.as_completed()
        if future:
            md_items = state.treat_output(future.result())

        # submit new job
        if state.cstep + state.workers <= state.tsteps:
            # chose ens and path for the next job
            md_items = state.prep_md_items(md_items)

            # submit job to scheduler
            futures.add(runner.submit_work(md_items))
            snapshot_end = tracemalloc.take_snapshot()
            # display_top_stats(snapshot_start, snapshot_end)

    # end client
    runner.stop()

def display_top_stats(snapshot_start, snapshot_end):
    print("[ Top 10 memory usage differences ]")
    top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
    for stat in top_stats[:10]:
        print(stat)