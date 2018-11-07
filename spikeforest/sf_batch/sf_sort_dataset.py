from kbucket import client as kb
import spikeinterface as si
import spikeforest as sf
import mlprocessors as mlpr
import os

class MountainSort4(mlpr.Processor):
    NAME='MountainSort4'
    VERSION='4.0.1'
    
    dataset_dir=mlpr.Input('Directory of dataset',directory=True)
    firings_out=mlpr.Output('Output firings file')
    
    detect_sign=mlpr.IntegerParameter('Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius=mlpr.FloatParameter('Use -1 to include all channels in every neighborhood')
    freq_min=mlpr.FloatParameter(optional=True,default=300,description='Use 0 for no bandpass filtering')
    freq_max=mlpr.FloatParameter(optional=True,default=6000,description='Use 0 for no bandpass filtering')
    whiten=mlpr.BoolParameter(optional=True,default=True,description='Whether to do channel whitening as part of preprocessing')
    clip_size=mlpr.IntegerParameter(optional=True,default=50,description='')
    detect_threshold=mlpr.FloatParameter(optional=True,default=3,description='')
    detect_interval=mlpr.IntegerParameter(optional=True,default=10,description='Minimum number of timepoints between events detected on the same channel')
    noise_overlap_threshold=mlpr.FloatParameter(optional=True,default=0.15,description='Use None for no automated curation')
    
    def run(self):
        recording=si.MdaRecordingExtractor(self.dataset_dir)
        num_workers=os.environ.get('NUM_WORKERS',None)
        sorting=sf.sorters.mountainsort4(
            recording=recording,
            detect_sign=self.detect_sign,
            adjacency_radius=self.adjacency_radius,
            freq_min=self.freq_min,
            freq_max=self.freq_max,
            whiten=self.whiten,
            clip_size=self.clip_size,
            detect_threshold=self.detect_threshold,
            detect_interval=self.detect_interval,
            noise_overlap_threshold=self.noise_overlap_threshold,
            num_workers=num_workers
        )
        si.MdaSortingExtractor.writeSorting(sorting=sorting,save_path=self.firings_out)
        
Processors=dict(
    MountainSort4=MountainSort4
)
        
def sf_sort_dataset(sorter,dataset):
    dsdir=dataset['directory']
    sorting_params=sorter['params']
    processor_name=sorter['processor_name']
    if processor_name in Processors:
        SS=Processors[processor_name]
    else:
        raise Exception('No such sorter: '+processor_name)
        
    outputs=SS.execute(
        dataset_dir=dsdir,
        firings_out=dict(ext='.mda'),
        **sorting_params
    ).outputs
    result=dict(
        dataset_name=dataset['name'],
        dataset_dir=dsdir,
        firings_true=dsdir+'/firings_true.mda',
        sorting_params=sorting_params,
        sorting_processor_name=SS.NAME,
        sorting_processor_version=SS.VERSION,
        firings=outputs['firings_out']
    )
    kb.saveFile(outputs['firings_out'])
    return result
