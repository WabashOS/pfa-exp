import numpy as np
from collections import defaultdict
import random
import argparse

def gen_graph(n_nodes, n_edges):
    graph = defaultdict(int)

    for i in range(0, n_edges):
        a = random.randint(0, n_nodes)
        b = random.randint(0, n_nodes)

        # a has link to b
        if a != b:
            graph[(a, b)] = 1

    return graph

def calc_matrix(graph, n, d):
    mat = np.zeros((n, n))

    for j in range(0, n):
        # find all outbound links from j
        column = np.array(
                [graph[(j, i)] for i in range(0, n)],
                dtype=np.float64)
        nout = np.sum(column)
        if nout > 0:
            column = column / nout
        else:
            column = np.ones(n, dtype=np.float64) * (1.0/n)
        mat[:,j] = column

    return d * mat + ((1 - d) / n) * np.ones((n, n), dtype=np.float64)

def pagerank(mat, eps):
    n = mat.shape[0]
    last_v = np.ones(n, dtype=np.float64) * (1.0/n)
    v = mat.dot(last_v)

    while np.linalg.norm(v - last_v, 2) > eps:
        last_v = v
        v = mat.dot(v)

    return v

def dump_header_data(f, name, mat):
    head = "double {}[{}] = {{".format(name, mat.size)
    s = head + ", ".join(str(val) for val in np.nditer(mat)) + "};\n"
    f.write(s)

def main():
    parser = argparse.ArgumentParser("Generate PageRank input data")
    parser.add_argument("--nodes", dest="n_nodes", type=int,
            default=32768, help="number of nodes in graph")
    parser.add_argument("--edges", dest="n_edges_per_node", type=int,
            default=4, help="avg. number of edges per node")
    parser.add_argument("--damp", dest="dampen", type=float,
            default=0.85, help="damping factor for pagerank calculation")
    parser.add_argument("--error", dest="error", type=float,
            default=1e-8, help="error at which ranks are considered converged")
    parser.add_argument("--binary", dest="binary", action="store_true",
            help="output in binary format")
    parser.add_argument("--pagesize", dest="pagesize", type=int,
            default=4096, help="page size")
    parser.add_argument("outfile", help="file to output to")
    args = parser.parse_args()

    graph = gen_graph(args.n_nodes, args.n_nodes * args.n_edges_per_node)
    mat = calc_matrix(graph, args.n_nodes, args.dampen)
    ranks = pagerank(mat, args.error)

    with open(args.outfile, "w") as f:
        if args.binary:
            mat.tofile(f)
            ranks.tofile(f)
        else:
            f.write("#define N {}\n".format(args.n_nodes))
            f.write("#define ERR {}\n".format(args.error))
            dump_header_data(f, "pr_matrix", mat)
            dump_header_data(f, "expected_ranks", ranks)

if __name__ == "__main__":
    main()
