export interface ProductSpecs {
  CPU?: string;
  RAM?: string;
  'Bộ nhớ/RAM'?: string;
  'Màn hình'?: string;
  'Độ phân giải'?: string;
  Pin?: string;
  HĐH?: string;
  Hãng?: string;
  summary?: string;
  [key: string]: string | undefined;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  category: 'PHONE' | 'LAPTOP';
  brand: string;
  part_number?: string;
  specs?: ProductSpecs;
  created_at?: string;
  updated_at?: string;
}
