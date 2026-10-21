import * as Device from 'expo-device';
import * as Location from 'expo-location';

export type ToolName = 'getCurrentLocation' | 'getDeviceContext' | 'getCurrentTime' | 'calculate';

export type ToolExecution = {
  name: ToolName;
  description: string;
  parameters?: Record<string, unknown>;
  execute: (args?: Record<string, unknown>) => Promise<string>;
};

export const getCurrentTime = (): string => {
  const now = new Date();
  let timeZone = 'Unknown';
  try {
    timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Unknown';
  } catch {
    // The clock and UTC offset remain available without timezone-name support.
  }
  return JSON.stringify({
    localTime: now.toLocaleTimeString(),
    localDate: now.toLocaleDateString(),
    localDateTime: now.toString(),
    utcDateTime: now.toISOString(),
    timeZone,
    utcOffsetMinutes: -now.getTimezoneOffset(),
    source: 'Clock and timezone settings of the device running the app',
  });
};

export const getDeviceContext = (): string => {
  const brand = Device.brand ?? 'Unknown brand';
  const model = Device.modelName ?? 'device';
  const os = Device.osVersion ?? 'unknown OS';

  return `This device is a ${brand} ${model} running ${Device.osName ?? 'an unknown OS'} ${os}.`;
};

export const getCurrentLocation = async (): Promise<string> => {
  const { status } = await Location.requestForegroundPermissionsAsync();

  if (status !== 'granted') {
    return 'Location permission was denied, so I could not fetch the current geographic position.';
  }

  const location = await Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.Balanced,
  });

  return `I checked your current location: latitude ${location.coords.latitude.toFixed(
    4,
  )}, longitude ${location.coords.longitude.toFixed(4)}.`;
};

// Fixed operations only: model inputs are never evaluated as JavaScript.
export const calculate = (args?: Record<string, unknown>): string => {
  const { operation, a, b } = args ?? {};
  if (Object.keys(args ?? {}).some((key) => !['operation', 'a', 'b'].includes(key))) {
    throw new Error('Calculator accepts only operation, a, and b.');
  }
  if (typeof a !== 'number' || !Number.isFinite(a) || typeof b !== 'number' || !Number.isFinite(b)) {
    throw new Error('Calculator requires finite numeric operands a and b.');
  }
  let result: number;
  switch (operation) {
    case 'add': result = a + b; break;
    case 'subtract': result = a - b; break;
    case 'multiply': result = a * b; break;
    case 'divide':
      if (b === 0) throw new Error('Cannot divide by zero.');
      result = a / b; break;
    case 'power': result = a ** b; break;
    case 'percentage': result = (a / 100) * b; break;
    default: throw new Error('Choose add, subtract, multiply, divide, power, or percentage.');
  }
  if (!Number.isFinite(result)) throw new Error('Calculation has no finite real result.');
  return JSON.stringify({ operation, a, b, result, precision: 'JavaScript floating-point arithmetic' });
};

export const toolRegistry: Record<ToolName, ToolExecution> = {
  calculate: {
    name: 'calculate',
    description: 'Calculate arithmetic using finite numbers a and b. Operations: add (a+b), subtract (a-b), multiply (a*b), divide (a/b), power (a raised to b), percentage (a percent of b). Use for arithmetic rather than guessing. Chain calls for multi-step calculations. Uses floating-point numbers.',
    parameters: {
      type: 'object',
      properties: {
        operation: { type: 'string', enum: ['add', 'subtract', 'multiply', 'divide', 'power', 'percentage'] },
        a: { type: 'number', description: 'First operand; percentage amount for percentage.' },
        b: { type: 'number', description: 'Second operand; base amount for percentage.' },
      },
      required: ['operation', 'a', 'b'], additionalProperties: false,
    },
    execute: async (args) => calculate(args),
  },
  getCurrentTime: {
    name: 'getCurrentTime',
    description: 'Read the device clock: current local date/time, timezone, and UTC offset. Use for current time/date questions or calculations relative to today. The clock does not look up event dates. localTime and localDate are local; utcDateTime is UTC. Takes no arguments.',
    execute: async () => getCurrentTime(),
  },
  getCurrentLocation: {
    name: 'getCurrentLocation',
    description: 'Fetch current latitude and longitude after requesting foreground location permission. Requires location services. Does not provide maps or nearby-business search. Takes no arguments.',
    execute: getCurrentLocation,
  },
  getDeviceContext: {
    name: 'getDeviceContext',
    description: 'Read available device brand, model, operating system, and OS version. Browser metadata may be limited. Does not test hardware capabilities such as GPS, Wi-Fi, camera, or microphone. Takes no arguments.',
    execute: async () => getDeviceContext(),
  },
};
