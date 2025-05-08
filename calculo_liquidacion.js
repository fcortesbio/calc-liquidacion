// === FUNCTION DEFINITIONS ===

/**
 * To calculate the number of dates between a start date and an end date
 * arguments are arrays in the format: [YYYY, MM, DD]
 */
function daysBetween(startDateArray, endDateArray) {
  // Create Date objects from the input arrays (month is 0-indexed)
  const startDate = new Date(
    startDateArray[0],
    startDateArray[1] - 1,
    startDateArray[2]
  );
  const endDate = new Date(
    endDateArray[0],
    endDateArray[1] - 1,
    endDateArray[2]
  );

  // Calculate the difference in milliseconds
  const differenceInMilliseconds = endDate.getTime() - startDate.getTime();

  // Convert milliseconds to days (1 day = 24 * 60 * 60 * 1000 milliseconds)
  const differenceInDays =
    Math.round(differenceInMilliseconds / (1000 * 60 * 60 * 24)) + 1;

  return differenceInDays;
}

/**
 * To operate with days over a date
 */
function addDaysToDate(startDateArray, daysToAdd) {
    // Create a Date object from the input array (month is 0-indexed)
    const startDate = new Date(startDateArray[0], startDateArray[1] - 1, startDateArray[2]);
  
    // Get the time in milliseconds and add the milliseconds for the given number of days
    const newTimeMilliseconds = startDate.getTime() + (daysToAdd * 24 * 60 * 60 * 1000);
  
    // Create a new Date object from the new time in milliseconds
    const newDate = new Date(newTimeMilliseconds);
  
    // Extract the year, month (add 1 for 1-based indexing), and day
    const newYear = newDate.getFullYear();
    const newMonth = newDate.getMonth() + 1;
    const newDay = newDate.getDate();
  
    return [newYear, newMonth, newDay];
  }


// today as an Array formatted date
const nowArr = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth() + 1; // add +1, months are 0-indexed
  const day = today.getDate();
  return [year, month, day];
};

// === Initial variables ===
const salary = 2_100_000;
const aux_transp_2023 = 140_606;
const aux_transp_2024 = 162_000;

console.log("--- LIQUIDACIÓN DETALLADA ---");

// === Calculate days worked ==
// 2023
const hiring_date = [2023, 4, 17];
const end_date_2023 = [2023, 12, 31];
const days_worked_2023 = daysBetween(hiring_date, end_date_2023);
console.log(`Días laborados 2023: ${days_worked_2023}`);

// 2024
const start_date_2024 = [2024, 1, 1];
const termination_date = [2024, 2, 17];
const days_worked_2024 = daysBetween(start_date_2024, termination_date);
console.log(`Días laborados 2024: ${days_worked_2024}`);

// === Cesantias ===



const lim_cesantias = [2024, 2, 14];

const lim_prima_salarial = addDaysToDate(termination_date, 15)