import torch 
import sys 

from torch_geometric.utils import degree

sys.path.insert(0, '/mnt/raid0_24TB/isaiah/code/GRL')
import rl_module
import load_graphs as lg

def generate_walks(Agent):
    non_orphans = (degree(Agent.data.edge_index[0], num_nodes=Agent.data.num_nodes) > 1).nonzero()
    non_orphans = non_orphans.T.numpy()[0]

    walks = Agent.generate_walks(non_orphans, strings=False)
    return walks.flatten().numpy()

def prep_agent(wlen, nw, loader=lg.load_cora):
    data = loader()

    Agent = rl_module.Q_Walker(data, episode_len=wlen, num_walks=nw)
    Agent.remove_direction()
    Agent.update_action_map()

    return Agent

def build_mem_info(Agent):
    csr = Agent._get_csr()
    memsize = [0] * Agent.data.num_nodes
    prev_addr = 0

    for i in range(csr.shape[0]):
        ns = csr[i].data.shape[0]
        ns += prev_addr
        prev_addr = memsize[i] = ns

    return memsize

'''
Assumes program memory is organized as follows
Array of pointers to list of neighbors in contiguous CSR
Contiguous CSR of neighbors 
Data (assumed 256B per node) optional
'''
def translate_to_din(walks, mem_info, node_data_size):
    neigh_ptr_addr = len(mem_info) * 4
    
    # Optional if also reading node data
    data_ptr_addr = neigh_ptr_addr + mem_info[-1] * 4
    data_start_addr = data_ptr_addr + len(mem_info) * 4
    
    accesses = []
    for node in walks:
        # Optional: load in data for node in focus
        if node_data_size:
            accesses.append(data_ptr_addr + node*4)
            accesses += [
                data_start_addr+node_data_size*node+i 
                for i in range(node_data_size)
            ]

        # First access data ptr for that node to get 
        # start and end of neighbor list in CSR list
        accesses.append(node*4)
        accesses.append((node+1)*4)

        # Then access the neighbor list
        if node > 0:
            accesses += [
                neigh_ptr_addr+b*4 
                for b in range(mem_info[node-1], mem_info[node])
            ]
        else:
            accesses += [
                neigh_ptr_addr+b*4 
                for b in range(mem_info[node])
            ]
    
    print(str(len(accesses)) + ' accesses')
    return accesses

'''
Makes dinero trace from generated random walks
uses -informat d 
'''
def main(loader=lg.load_cora, wlen=5, nw=1, node_data_size=None, fname=None):
    a = prep_agent(wlen, nw, loader=loader)
    mi = build_mem_info(a)
    w = generate_walks(a)
    accesses = translate_to_din(w, mi, node_data_size)

    outstr = '\n'.join([
        '0 ' + hex(a) for a in accesses
    ])

    if not fname:
        print(outstr)
        return 

    with open(fname, 'w+') as f:
        f.write(outstr)

'''
main(fname='cora_no_data.din')
main(fname='cora_w_data.din', node_data_size=256)
'''
main(fname='citeseer_no_data.din', wlen=5, nw=1, loader=lg.load_citeseer)
#main(fname='citeseer_w_data.din', loader=lg.load_citeseer, node_data_size=256)