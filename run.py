import config as cfg

if cfg.IN_AWS_LAMBDA:
    import sys
    import runpy
    # sys.path.insert(0, '')
    sys.argv = ['awslambdaric', 'lambda_function.lambda_handler']
    runpy.run_module('awslambdaric', run_name='__main__') 
else:
    import lambda_function
    lambda_function.telegram_long_polling()