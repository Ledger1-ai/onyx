
export interface IJobAdapter {
    id: string;
    name: string;
    data: any;
    log: (msg: string) => void;
}
