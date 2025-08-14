// Copyright (c) 2024, Maxim Sysoev and contributors
// For license information, please see license.txt

// calculateControlDigit calculates 10th (control digit) from the first 9 digits
const calculateControlDigit = rnokpp => {
    const weights = [-1, 5, 7, 9, 4, 6, 10, 5, 7];
    const sum = weights.reduce((acc, weight, index) => {
        const digit = parseInt(rnokpp[index], 10);
        return acc + (digit * weight);
    }, 0);

    const checksum = sum % 11;
    return checksum === 10 ? 0 : checksum;
};

function addDays(date, days) {
    // Create a new Date object based on the input date
    const result = new Date(date);
    // Use the setDate method to add the specified number of days
    result.setDate(result.getDate() + days);
    // Return the updated Date object
    return result;
}
function taxCodeInfo(tax_code) {
    if (tax_code.length != 10) {
        return { "error": "ErrInvalidLength" };
    }
    genderDigit = (tax_code[8]);  // gender digit
    controlDigit = (tax_code[9]); // control digit
    const gender = genderDigit % 2 == 0 ? "Female" : "Male";
    if (controlDigit != calculateControlDigit(tax_code)) {
        return { "error": "ErrInvalidControlDigit" };
    }
    numberOfDaysSinceBaseDate = tax_code[0] * 10000 + tax_code[1] * 1000 + tax_code[2] * 100 + tax_code[3] * 10 + tax_code[4] * 1
    numberOfDaysSinceBaseDate -= 1;
    birthday = addDays("1900/1/1", numberOfDaysSinceBaseDate);
    return {
        "gender": gender,
        "birthday": birthday,
    }
}