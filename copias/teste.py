def get_program_parameters():
    import argparse
    description = ''
    epilogue = '''

    '''
    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('fn1', nargs='?', default=None, help='Patient_1_scar.vtk.')
    parser.add_argument('fn2', nargs='?', default=None, help='Patient_1_surf.vtk')

    args = parser.parse_args()
    print(type(args))
    # if len(args) > 0:
    #     return args.fn1, args.fn2
    # else:
    #     raise ValueError(f"Argumento não encontrado")
    
get_program_parameters()