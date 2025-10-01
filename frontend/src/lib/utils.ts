type AnyObject = { [key: string]: any };

const toSnakeCase = (str: string) =>
  str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);

export const keysToSnakeCase = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => keysToSnakeCase(item)) as unknown as T;
  }

  const newObj = {} as AnyObject;
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      newObj[toSnakeCase(key)] = keysToSnakeCase(obj[key]);
    }
  }

  return newObj as T;
};
