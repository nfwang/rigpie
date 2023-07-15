def flattenlist(array):
    ''' Flatten a list using pythons ':' for list ranges into discreet elements. '''
    flattened_list = []
    for item in array:
        node, ids = item.split(".vtx")
        
        if ":" in ids:
            start = int(ids.split(":")[0][1:])
            end = int(ids.split(":")[1][:-1])

            for ii in range(start, end):
                flattened_list.append("{}.vtx[{}]".format(node, ii))
        else:
            flattened_list.append("{}.vtx{}".format(node, ids))
            
    return flattened_list
    
